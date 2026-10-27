import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from components.importer import ImportRowError, import_csv
from components.models import ComponentCategory


class Command(BaseCommand):
    help = "Import components from CSV files, using the same rules as the admin importer."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            help="A CSV file, or a directory when --all is used.",
        )
        parser.add_argument(
            "--type",
            choices=ComponentCategory.values,
            help="Component type for a single CSV file.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Import cpus.csv, motherboards.csv, and coolers.csv from a directory.",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if options["all"]:
            self._import_directory(path)
        else:
            if not options["type"]:
                raise CommandError("Use --type <category> or --all with a directory.")
            self._import_file(path, options["type"])

    def _import_file(self, path, category):
        if not path.is_file():
            raise CommandError(f"File not found: {path}")

        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            try:
                success, errors = import_csv(csv.DictReader(csv_file), category)
            except ImportRowError as exc:
                raise CommandError(str(exc)) from exc

        self.stdout.write(f"{path.name} ({category}): {success} row(s) imported")
        for error in errors:
            self.stderr.write(self.style.ERROR(error))
        if errors:
            raise CommandError(f"{len(errors)} row(s) failed in {path.name}")

    def _import_directory(self, directory):
        if not directory.is_dir():
            raise CommandError(f"Directory not found: {directory}")

        targets = [
            ("cpus.csv", ComponentCategory.CPU),
            ("motherboards.csv", ComponentCategory.MOTHERBOARD),
            ("coolers.csv", ComponentCategory.COOLER),
            ("ram.csv", ComponentCategory.RAM),
        ]
        found = False
        for filename, category in targets:
            path = directory / filename
            if path.is_file():
                found = True
                self._import_file(path, category)

        if not found:
            raise CommandError(
                f"No cpus.csv, motherboards.csv, coolers.csv, or ram.csv found in {directory}"
            )
