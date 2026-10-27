from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from components.models import CoolerSpec, CpuSpec
from components.tests.factories import make_cpu

COOLER_CSV = (
    "mpn,brand,model,msrp,coolerType,supportedSockets,tdpRatingWatts,heightMm,"
    "ramClearanceMm,radiatorSizeMm,radiatorThicknessMm,radiatorLengthMm,"
    "radiatorWidthMm,fanCount,fanSizeMm,noiseDbMax,weightG,powerConnector\n"
    'COOL-ADMIN-1,Noctua,NH-D15,109.95,Air,"AM4, AM5, LGA 1700",250,165,32,'
    ',,,,2,140,24.6,1320,4-pin PWM\n'
)

CPU_CSV = (
    "mpn,brand,model,msrp,socket,coreCount,threadCount,baseClockGhz,"
    "boostClockGhz,tdpWatts,maxPowerWatts,hasIntegratedGpu,includedCooler\n"
    "CPU-ADMIN-1,AMD,Ryzen 5 7600X,299.00,AM5,6,12,4.7,5.3,105,142,true,false\n"
)


class AdminCsvUploadTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        self.client.force_login(self.user)

    def _upload(self, model_name, component_type, content):
        upload = SimpleUploadedFile(
            "components.csv", content.encode("utf-8"), content_type="text/csv"
        )
        return self.client.post(
            f"/admin/components/{model_name}/upload-csv/",
            {"component_type": component_type, "csv_file": upload},
        )

    def test_cooler_changelist_has_import_button_and_excludes_other_categories(self):
        make_cpu(model="Ryzen 9 5950X")

        response = self.client.get(reverse("admin:components_cooler_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Import CSV")
        self.assertNotContains(response, "Ryzen 9 5950X")

    def test_uploading_cooler_csv_creates_spec_and_sockets(self):
        response = self._upload("cooler", "Cooler", COOLER_CSV)

        self.assertEqual(response.status_code, 302)
        spec = CoolerSpec.objects.get()
        self.assertEqual(spec.component.mpn, "COOL-ADMIN-1")
        self.assertEqual(spec.height_mm, 165)
        self.assertEqual(
            sorted(spec.supported_sockets.values_list("name", flat=True)),
            ["AM4", "AM5", "LGA1700"],
        )

    def test_uploading_cpu_csv_uses_new_power_field(self):
        response = self._upload("cpu", "CPU", CPU_CSV)

        self.assertEqual(response.status_code, 302)
        spec = CpuSpec.objects.get()
        self.assertEqual(spec.socket.name, "AM5")
        self.assertEqual(spec.max_power_watts, 142)
        self.assertEqual(spec.effective_power_watts, 142)

    def test_invalid_csv_row_is_reported_and_not_saved(self):
        broken = CPU_CSV.replace("105,142", "oops,142")
        response = self._upload("cpu", "CPU", broken)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CpuSpec.objects.exists())
