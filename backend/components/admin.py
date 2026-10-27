import csv

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .importer import ImportRowError, import_csv
from .models import (
    Component,
    Cooler,
    CoolerSpec,
    Cpu,
    CpuSpec,
    Motherboard,
    MotherboardSpec,
)


class CpuSpecInline(admin.StackedInline):
    model = CpuSpec


class MotherboardSpecInline(admin.StackedInline):
    model = MotherboardSpec


class CoolerSpecInline(admin.StackedInline):
    model = CoolerSpec
    filter_horizontal = ("supported_sockets",)


# --- 1. THE MASTER COMPONENT ADMIN ---
@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "mpn", "msrp", "category")
    search_fields = ("mpn", "brand", "model")
    list_filter = ("category", "brand")

    # Share the CSV button template across all child models
    change_list_template = "admin/components/component/change_list.html"

    # Remove the "+ Add" button from the master "All Components" page
    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        # Generate a unique URL name for each model to prevent conflicts
        url_name = f"{self.model._meta.app_label}_{self.model._meta.model_name}_upload_csv"
        custom_urls = [
            path("upload-csv/", self.upload_csv, name=url_name),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            component_type = request.POST.get("component_type", "")

            if not csv_file or not csv_file.name.lower().endswith(".csv"):
                messages.error(request, "Please upload a valid CSV file.")
                return redirect("..")

            file_data = csv_file.read().decode("utf-8-sig")
            reader = csv.DictReader(file_data.splitlines())

            try:
                success_count, errors = import_csv(reader, component_type)
            except ImportRowError as exc:
                messages.error(request, str(exc))
                return redirect("..")

            if success_count:
                messages.success(
                    request,
                    f"Successfully imported/updated {success_count} {component_type} row(s).",
                )
            for error in errors[:10]:
                messages.error(request, error)
            if len(errors) > 10:
                messages.error(request, f"...and {len(errors) - 10} more error(s).")

            return redirect("..")

        return render(request, "admin/csv_upload.html")


# --- 2. THE CPU ADMIN ---
# Child admins inherit the CSV import + shared list behavior.
@admin.register(Cpu)
class CpuAdmin(ComponentAdmin):
    list_display = ("brand", "model", "mpn", "msrp")
    list_filter = ("brand",)
    inlines = [CpuSpecInline]

    # Hide the category dropdown field in the UI completely
    exclude = ("category",)

    def has_add_permission(self, request):
        return True

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.category = "CPU"
        super().save_model(request, obj, form, change)


# --- 3. THE MOTHERBOARD ADMIN ---
@admin.register(Motherboard)
class MotherboardAdmin(ComponentAdmin):
    list_display = ("brand", "model", "mpn", "msrp")
    list_filter = ("brand",)
    inlines = [MotherboardSpecInline]

    exclude = ("category",)

    def has_add_permission(self, request):
        return True

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.category = "Motherboard"
        super().save_model(request, obj, form, change)


# --- 4. THE COOLER ADMIN ---
@admin.register(Cooler)
class CoolerAdmin(ComponentAdmin):
    list_display = ("brand", "model", "mpn", "msrp")
    list_filter = ("brand",)
    inlines = [CoolerSpecInline]

    exclude = ("category",)

    def has_add_permission(self, request):
        return True

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.category = "Cooler"
        super().save_model(request, obj, form, change)
