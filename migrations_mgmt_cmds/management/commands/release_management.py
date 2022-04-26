from os.path import join, basename
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.module_loading import import_string
from django.core.management.base import CommandParser, DjangoHelpFormatter

from migrations_mgmt_cmds.storage import migrations_releases_storage

__all__ = ["Command", "default_sort_date"]


def default_sort_date(filename):
    try:
        return int(migrations_releases_storage.get_created_time(filename).timestamp())
    except NotImplementedError:
        return int(migrations_releases_storage.get_modified_time(filename).timestamp())


class Command(BaseCommand):
    help = "Manage release files."
    sorted_files_by_date = None

    def create_parser(self, prog_name, subcommand, **kwargs):
        """
        Create and return the ``ArgumentParser`` which will be used to
        parse the arguments to this command.
        """
        parser = CommandParser(
            prog="%s %s" % (basename(prog_name), subcommand),
            description=self.help or None,
            formatter_class=DjangoHelpFormatter,
            missing_args_message=getattr(self, "missing_args_message", None),
            called_from_command_line=getattr(self, "_called_from_command_line", None),
            **kwargs,
        )
        parser.add_argument(
            "--settings",
            help=(
                "The Python path to a settings module, e.g. "
                '"myproject.settings.main". If this isn\'t provided, the '
                "DJANGO_SETTINGS_MODULE environment variable will be used."
            ),
        )
        parser.add_argument(
            "--pythonpath",
            help='A directory to add to the Python path, e.g. "/home/djangoprojects/">',
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Don't colorize the command output.",
        )
        parser.add_argument(
            "--force-color",
            action="store_true",
            help="Force colorization of the command output.",
        )
        parser.add_argument(
            "-v",
            "--verbosity",
            action="store",
            dest="verbosity",
            default=2,
            type=int,
            choices=[0, 1, 2],
            help="Verbosity level; 0=no output, 1=minimal output, 2=normal output",
        )
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        """
        Method to add arguments to be parsed by terminal (command line).
        """
        parser.add_argument(
            "--display-list",
            action="store_true",
            dest="display_list",
            help="Define if the command should display the ordered list of releases by date found.",
        )
        parser.add_argument(
            "--display-last",
            action="store_true",
            dest="display_last",
            help="Define if the command should display the last release file created.",
        )
        parser.add_argument(
            "--recursive-search",
            action="store_true",
            dest="recursive_search",
            help="Define if the search for files in `--display-list` or `--display-last` should be "
            "recursive.",
        )
        parser.add_argument(
            "--disable-release",
            action="store",
            dest="disable_release",
            default=None,
            help="Nominates the release file's path to disable it from search. It will rename the"
            " extension of file to .old disabling it from search but keeping the file.",
        )
        parser.add_argument(
            "--delete-release",
            action="store",
            dest="delete_release",
            default=None,
            help="Nominates the release file's path to permanent delete it.",
        )

    def get_files_list(self, recursive=False, path=""):
        files_list = []
        if recursive:
            for directory in migrations_releases_storage.listdir(path)[0]:
                files_list += self.get_files_list(recursive=recursive, path=join(path, directory))

        for filename in migrations_releases_storage.listdir(path)[1]:
            files_list.append(join(path, filename))

        return files_list

    def handle(self, *args, **options):
        display_list = options["display_list"]
        display_last = options["display_last"]
        disable_release_file = options["disable_release"]
        delete_release_file = options["delete_release"]
        recursive = options["recursive_search"]
        verbosity = options["verbosity"]

        if display_list or display_last:
            sorting_setting = getattr(settings, "MIGRATIONS_RELEASES_SORTING", None)
            key = import_string(sorting_setting) if sorting_setting else default_sort_date

            # Get sorted list of JSON files only.
            self.sorted_files_by_date = sorted(
                [f for f in self.get_files_list(recursive) if f[-5:].lower() == ".json"],
                key=key,
            )

        if display_list and verbosity:
            # Show header
            if verbosity > 1:
                self.stdout.write(self.style.MIGRATE_HEADING("Listing files by creation date:"))

            # Show list of files created ordered by creation date.
            for item in self.sorted_files_by_date:
                self.stdout.write(item)

        if display_last and verbosity:
            # Show header
            if verbosity > 1:
                self.stdout.write(self.style.MIGRATE_HEADING("Last file created: "))

            # Show last file created
            self.stdout.write(self.sorted_files_by_date[-1])

        if disable_release_file:
            # Check if filename is json
            if not disable_release_file[-5:].lower() == ".json":
                raise CommandError(
                    "Filename {} informed at `--disable-release` should be of type JSON!".format(
                        disable_release_file
                    )
                )

            # Check if path exists
            if not migrations_releases_storage.exist(disable_release_file):
                raise CommandError("No release file {!r}".format(disable_release_file))

            # Open file content
            file_object = migrations_releases_storage.open(disable_release_file, "rb")

            # Save new content with extension `.disabled`
            migrations_releases_storage.save(
                disable_release_file + ".disabled", content=file_object
            )

            # Delete old file.
            migrations_releases_storage.delete(disable_release_file)

            if verbosity > 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        "File `{}` changed to `{}` with success.".format(
                            disable_release_file, disable_release_file + ".disabled"
                        )
                    )
                )

        if delete_release_file:
            # Check if path exists
            if not migrations_releases_storage.exist(delete_release_file):
                raise CommandError("No release file {!r}".format(delete_release_file))

            # Delete old file.
            migrations_releases_storage.delete(delete_release_file)

            if verbosity > 1:
                self.stdout.write(
                    self.style.SUCCESS(
                        "File `{}` deleted with success.".format(delete_release_file)
                    )
                )
