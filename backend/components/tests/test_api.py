from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from components.tests.factories import make_cooler, make_cpu, make_motherboard


class CpuApiTests(APITestCase):
    def setUp(self):
        self.cpu = make_cpu(mpn="CPU-API-1", socket_name="AM5", max_power_watts=142)
        self.motherboard = make_motherboard()

    def test_only_cpus_are_returned(self):
        response = self.client.get(reverse("get_cpus"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mpn"], "CPU-API-1")
        self.assertEqual(response.data[0]["cpu_spec"]["socket"], "AM5")
        self.assertEqual(response.data[0]["cpu_spec"]["max_power_watts"], 142)
        self.assertEqual(response.data[0]["cpu_spec"]["effective_power_watts"], 142)

    def test_filter_by_socket(self):
        response = self.client.get(reverse("get_cpus"), {"socket": "am5"})
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse("get_cpus"), {"socket": "LGA1700"})
        self.assertEqual(response.data, [])


class MotherboardApiTests(APITestCase):
    def setUp(self):
        self.cpu = make_cpu()
        self.motherboard = make_motherboard(mpn="MB-API-1", socket_name="AM5")

    def test_only_motherboards_are_returned_with_nested_specs(self):
        response = self.client.get(reverse("get_motherboards"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mpn"], "MB-API-1")
        self.assertEqual(response.data[0]["specs"]["socket"], "AM5")
        self.assertEqual(response.data[0]["specs"]["form_factor"], "ATX")

    def test_filter_by_socket(self):
        response = self.client.get(reverse("get_motherboards"), {"socket": "AM5"})
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse("get_motherboards"), {"socket": "AM4"})
        self.assertEqual(response.data, [])


class CoolerApiTests(APITestCase):
    def setUp(self):
        self.cooler = make_cooler(
            mpn="COOL-API-1",
            socket_names=("AM4", "AM5", "LGA1700"),
        )
        self.aio = make_cooler(
            mpn="COOL-API-2",
            socket_names=("AM5",),
            cooler_type="AIO",
            height_mm=None,
            radiator_size_mm=360,
        )
        self.cpu = make_cpu()

    def test_only_coolers_are_returned(self):
        response = self.client.get(reverse("get_coolers"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        by_mpn = {row["mpn"]: row for row in response.data}
        self.assertEqual(
            sorted(by_mpn["COOL-API-1"]["specs"]["supported_sockets"]),
            ["AM4", "AM5", "LGA1700"],
        )
        self.assertEqual(by_mpn["COOL-API-1"]["specs"]["height_mm"], 165)
        self.assertIsNone(by_mpn["COOL-API-2"]["specs"]["height_mm"])
        self.assertEqual(by_mpn["COOL-API-2"]["specs"]["radiator_size_mm"], 360)

    def test_filter_by_socket(self):
        response = self.client.get(reverse("get_coolers"), {"socket": "LGA1700"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mpn"], "COOL-API-1")

    def test_filter_by_socket_is_case_insensitive(self):
        response = self.client.get(reverse("get_coolers"), {"socket": "lga1700"})
        self.assertEqual(len(response.data), 1)

    def test_filter_by_type(self):
        response = self.client.get(reverse("get_coolers"), {"type": "aio"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mpn"], "COOL-API-2")


class SocketApiTests(APITestCase):
    def test_returns_socket_names(self):
        make_cpu(socket_name="AM5")

        response = self.client.get(reverse("get_sockets"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row["name"] for row in response.data}
        self.assertIn("AM5", names)
        self.assertIn("LGA1700", names)  # seeded by the data migration
