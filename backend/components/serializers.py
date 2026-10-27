from rest_framework import serializers

from .models import Component, CoolerSpec, CpuSpec, MotherboardSpec, RamSpec, Socket


class SocketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Socket
        fields = ["id", "name"]


class CpuSpecSerializer(serializers.ModelSerializer):
    socket = serializers.SlugRelatedField(slug_field="name", read_only=True)
    effective_power_watts = serializers.IntegerField(read_only=True)

    class Meta:
        model = CpuSpec
        fields = [
            "socket",
            "core_count",
            "thread_count",
            "base_clock_ghz",
            "boost_clock_ghz",
            "tdp_watts",
            "max_power_watts",
            "effective_power_watts",
            "has_integrated_gpu",
            "included_cooler",
        ]


class ComponentCpuSerializer(serializers.ModelSerializer):
    # This automatically nests the CpuSpec inside the Component object
    cpu_spec = CpuSpecSerializer(read_only=True)

    class Meta:
        model = Component
        fields = ["id", "mpn", "brand", "model", "msrp", "category", "cpu_spec"]


class MotherboardSpecSerializer(serializers.ModelSerializer):
    socket = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = MotherboardSpec
        exclude = ("id", "component")  # Hide these to keep the JSON clean


class MotherboardSerializer(serializers.ModelSerializer):
    # This nests the specs inside the main motherboard JSON object
    specs = MotherboardSpecSerializer(source="motherboard_spec", read_only=True)

    class Meta:
        model = Component
        fields = ["id", "mpn", "brand", "model", "msrp", "category", "specs"]


class CoolerSpecSerializer(serializers.ModelSerializer):
    supported_sockets = serializers.SlugRelatedField(
        many=True, slug_field="name", read_only=True
    )

    class Meta:
        model = CoolerSpec
        exclude = ("id", "component")


class CoolerSerializer(serializers.ModelSerializer):
    specs = CoolerSpecSerializer(source="cooler_spec", read_only=True)

    class Meta:
        model = Component
        fields = ["id", "mpn", "brand", "model", "msrp", "category", "specs"]


class RamSpecSerializer(serializers.ModelSerializer):
    total_capacity_gb = serializers.IntegerField(read_only=True)
    first_word_latency_ns = serializers.FloatField(read_only=True)

    class Meta:
        model = RamSpec
        exclude = ("id", "component")


class RamSerializer(serializers.ModelSerializer):
    specs = RamSpecSerializer(source="ram_spec", read_only=True)

    class Meta:
        model = Component
        fields = ["id", "mpn", "brand", "model", "msrp", "category", "specs"]
