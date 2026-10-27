from django.test import SimpleTestCase, TestCase

from components.models import CoolerSpec, Cpu, Socket
from components.sockets import normalize_socket_name
from components.tests.factories import (
    make_cooler,
    make_cpu,
    make_motherboard,
    proxy_counts,
)


class SocketNormalizationTests(SimpleTestCase):
    def test_normalizes_common_spellings(self):
        cases = {
            "LGA 1700": "LGA1700",
            "lga-1700": "LGA1700",
            "1700": "LGA1700",
            "Socket AM5": "AM5",
            "am5": "AM5",
            "sTR5": "sTR5",
            "TR5": "sTR5",
            "SP5": "SP5",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_socket_name(raw), expected)

    def test_unknown_socket_is_preserved(self):
        self.assertEqual(normalize_socket_name("FutureSocket-1"), "FutureSocket-1")

    def test_blank_socket_returns_empty_string(self):
        self.assertEqual(normalize_socket_name("  "), "")
        self.assertEqual(normalize_socket_name(None), "")


class ProxyManagerTests(TestCase):
    def setUp(self):
        self.cpu = make_cpu()
        self.motherboard = make_motherboard()
        self.cooler = make_cooler()

    def test_each_proxy_only_returns_its_own_category(self):
        self.assertEqual(
            proxy_counts(),
            {"cpu": 1, "motherboard": 1, "cooler": 1, "all": 3},
        )

    def test_proxy_manager_filters_lookups(self):
        self.assertTrue(Cpu.objects.filter(pk=self.cpu.pk).exists())
        self.assertFalse(Cpu.objects.filter(pk=self.motherboard.pk).exists())


class CpuPowerTests(TestCase):
    def test_effective_power_falls_back_to_tdp(self):
        component = make_cpu(tdp_watts=105, max_power_watts=None)
        spec = component.cpu_spec
        self.assertEqual(spec.effective_power_watts, 105)

    def test_effective_power_prefers_sustained_power(self):
        component = make_cpu(tdp_watts=105, max_power_watts=142)
        spec = component.cpu_spec
        self.assertEqual(spec.effective_power_watts, 142)


class CoolerModelTests(TestCase):
    def test_supported_sockets_many_to_many(self):
        component = make_cooler(socket_names=("AM4", "AM5", "LGA1700"))
        spec = component.cooler_spec
        self.assertEqual(
            sorted(spec.supported_sockets.values_list("name", flat=True)),
            ["AM4", "AM5", "LGA1700"],
        )
        self.assertEqual(
            Socket.objects.get(name="AM5").cooler_specs.count(),
            1,
        )

    def test_aio_fields_can_be_null(self):
        component = make_cooler(
            mpn="AIO-1",
            socket_names=("AM5",),
            cooler_type="AIO",
            height_mm=None,
            radiator_size_mm=360,
            radiator_thickness_mm=30,
        )
        spec = component.cooler_spec
        self.assertIsNone(spec.height_mm)
        self.assertEqual(spec.radiator_size_mm, 360)
        self.assertEqual(CoolerSpec.objects.count(), 1)
