# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor

from migrations_mgmt_cmds.storage import migrations_releases_storage


class Command(BaseCommand):
    help = "Rollback a release."

    def add_arguments(self, parser):
        parser.add_argument(
            "--release",
            required=True,
            action="store",
            dest="release",
            help="Database state will be reverted to the state it was in at that release",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            default=True,
            help="Tells Django to NOT prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )
        parser.add_argument(
            "-v",
            "--verbosity",
            action="store",
            dest="verbosity",
            default=1,
            type=int,
            choices=[0, 1, 2, 3],
            help="Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, "
            "3=very verbose output",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Tells Django to NOT prompt the user for input of any kind.",
        )

    def handle(self, *args, **options):
        release_path = "{}.json".format(options["release"])

        if not migrations_releases_storage.exists(release_path):
            raise CommandError("No release file {!r}".format(release_path))

        targets = self.get_targets(release_path)

        self.verbosity = options.get("verbosity")
        self.interactive = options.get("interactive")

        # Get the database executor to work out which apps have migrations and which do not
        executor = self.get_executor(options.get("database"), self.migration_progress_callback)

        # Get the plan from database we're operating from
        plan = self.get_migration_plan(executor, targets)

        if not len(plan):
            raise CommandError("Nothing to rollback")

        for migration, applied in plan:
            if not applied:
                raise CommandError(
                    "Migration {} would be applied rather than reverted. This does not make sense and may not be safe.".format(
                        migration.name
                    )
                )

        if self.verbosity >= 1:
            self.stdout.write(self.style.MIGRATE_HEADING("Operations to perform:"))
            for migration, applied in plan:
                self.stdout.write("  Revert {} {}".format(migration.app_label, migration.name))

        if self.verbosity >= 1:
            self.stdout.write(self.style.MIGRATE_HEADING("Running migrations:"))

        executor.migrate(targets, plan, fake=False, fake_initial=False)

    @staticmethod
    def get_targets(release_path):
        with migrations_releases_storage.open(release_path, "r") as fp:
            release = json.load(fp)

        return release.items()

    @staticmethod
    def get_executor(database, callback=None):
        # Get the database we're operating from
        connection = connections[database]

        # Hook for backends needing any database preparation
        connection.prepare_database()

        # Return the executor from database with callback to process output.
        return MigrationExecutor(connection, callback)

    @staticmethod
    def get_migration_plan(executor, targets):
        # Before anything else, see if there's conflicting apps and drop out
        # hard if there are any
        conflicts = executor.loader.detect_conflicts()
        if conflicts:
            name_str = "; ".join(
                "%s in %s" % (", ".join(names), app) for app, names in conflicts.items()
            )
            raise CommandError(
                "Conflicting migrations detected; multiple leaf nodes in the "
                "migration graph: (%s).\nTo fix them run "
                "'python manage.py makemigrations --merge'" % name_str
            )

        return executor.migration_plan(targets)

    def migration_progress_callback(self, action, migration=None, fake=False):
        if self.verbosity >= 1:
            compute_time = self.verbosity > 1
            if action == "apply_start":
                if compute_time:
                    self.start = time.monotonic()
                self.stdout.write("  Applying %s..." % migration, ending="")
                self.stdout.flush()
            elif action == "apply_success":
                elapsed = " (%.3fs)" % (time.monotonic() - self.start) if compute_time else ""
                if fake:
                    self.stdout.write(self.style.SUCCESS(" FAKED" + elapsed))
                else:
                    self.stdout.write(self.style.SUCCESS(" OK" + elapsed))
            elif action == "unapply_start":
                if compute_time:
                    self.start = time.monotonic()
                self.stdout.write("  Unapplying %s..." % migration, ending="")
                self.stdout.flush()
            elif action == "unapply_success":
                elapsed = " (%.3fs)" % (time.monotonic() - self.start) if compute_time else ""
                if fake:
                    self.stdout.write(self.style.SUCCESS(" FAKED" + elapsed))
                else:
                    self.stdout.write(self.style.SUCCESS(" OK" + elapsed))
            elif action == "render_start":
                if compute_time:
                    self.start = time.monotonic()
                self.stdout.write("  Rendering model states...", ending="")
                self.stdout.flush()
            elif action == "render_success":
                elapsed = " (%.3fs)" % (time.monotonic() - self.start) if compute_time else ""
                self.stdout.write(self.style.SUCCESS(" DONE" + elapsed))
