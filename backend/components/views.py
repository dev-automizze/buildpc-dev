from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Cooler, Cpu, Motherboard, Socket
from .serializers import (
    ComponentCpuSerializer,
    CoolerSerializer,
    MotherboardSerializer,
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
def get_sockets(request):
    serializer = SocketSerializer(Socket.objects.all(), many=True)
    return Response(serializer.data)
