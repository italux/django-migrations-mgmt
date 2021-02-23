# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader


class Command(BaseCommand):

    help = "Shows all available migrations for the current project"

    def add_arguments(self, parser):
        parser.add_argument(
            "--release",
            required=True,
            action="store",
            dest="release",
            help="The release version to generate file",
        )
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        if getattr(settings, "MIGRATIONS_RELEASES_DIR", None):
            releases_dir = getattr(
                settings,
                "MIGRATIONS_RELEASES_DIR",
                os.path.join(settings.BASE_DIR, "MIGRATIONS_RELEASES_DIR"),
            )
        else:
            releases_dir = os.path.join(settings.BASE_DIR, "migrations/releases")

        db = options.get("database")

        # Load migration files from disk and their status from the database.
        # ignore_no_migrations=True will ignore apps without migrations
        loader = MigrationLoader(connections[db], ignore_no_migrations=True)
        graph = loader.graph
        app_names = sorted(loader.migrated_apps)

        leaf_migrations = {}
        for app_name in app_names:
            nodes = graph.leaf_nodes(app_name)
            if not nodes:
                continue

            if len(nodes) > 1:
                name_str = "; ".join("%s in %s" % (name, app) for app, name in nodes)
                raise CommandError(
                    "Conflicting migrations detected; multiple leaf nodes in the "
                    "migration graph: (%s).\nTo fix them run "
                    "'python manage.py makemigrations --merge'" % name_str
                )

            leaf_migrations[app_name] = graph.leaf_nodes(app_name)[0][1]

        result = json.dumps(
            leaf_migrations,
            sort_keys=True,
            indent=4,
            separators=(",", ": "),
        )

        if not os.path.exists(releases_dir):
            os.makedirs(releases_dir)

        with open(os.path.join(releases_dir, "{}.json".format(options["release"])), "w") as fp:
            fp.write(result)
