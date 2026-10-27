from django.db.models import F
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Cooler, Cpu, Motherboard, Ram, Socket
from .serializers import (
    ComponentCpuSerializer,
    CoolerSerializer,
    MotherboardSerializer,
    RamSerializer,
    SocketSerializer,
)


@api_view(["GET"])
def get_cpus(request):
    # The Cpu manager already scopes this queryset to category="CPU".
    cpus = Cpu.objects.select_related("cpu_spec__socket")

    socket = request.query_params.get("socket")
    if socket:
        cpus = cpus.filter(cpu_spec__socket__name__iexact=socket)

    serializer = ComponentCpuSerializer(cpus, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_motherboards(request):
    # The Motherboard manager already scopes this queryset to category="Motherboard".
    motherboards = Motherboard.objects.select_related("motherboard_spec__socket")

    socket = request.query_params.get("socket")
    if socket:
        motherboards = motherboards.filter(motherboard_spec__socket__name__iexact=socket)

    serializer = MotherboardSerializer(motherboards, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_coolers(request):
    # The Cooler manager already scopes this queryset to category="Cooler".
    coolers = Cooler.objects.select_related("cooler_spec").prefetch_related(
        "cooler_spec__supported_sockets"
    )

    socket = request.query_params.get("socket")
    if socket:
        coolers = coolers.filter(
            cooler_spec__supported_sockets__name__iexact=socket
        ).distinct()

    cooler_type = request.query_params.get("type")
    if cooler_type:
        coolers = coolers.filter(cooler_spec__cooler_type__iexact=cooler_type)

    serializer = CoolerSerializer(coolers, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_ram(request):
    # The Ram manager already scopes this queryset to category="RAM".
    ram = Ram.objects.select_related("ram_spec").annotate(
        total_gb=F("ram_spec__capacity_gb") * F("ram_spec__module_count")
    )

    memory_type = request.query_params.get("memory_type")
    if memory_type:
        ram = ram.filter(ram_spec__memory_type__iexact=memory_type)

    form_factor = request.query_params.get("form_factor")
    if form_factor:
        ram = ram.filter(ram_spec__form_factor__iexact=form_factor)

    min_capacity = request.query_params.get("min_capacity_gb")
    if min_capacity:
        try:
            ram = ram.filter(total_gb__gte=int(min_capacity))
        except ValueError:
            return Response(
                {"detail": "min_capacity_gb must be an integer."}, status=400
            )

    # Consumer platforms should not be offered registered server memory.
    if request.query_params.get("registered", "").lower() in {"false", "0", "no"}:
        ram = ram.filter(ram_spec__registered=False)

    serializer = RamSerializer(ram, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_sockets(request):
    serializer = SocketSerializer(Socket.objects.all(), many=True)
    return Response(serializer.data)
