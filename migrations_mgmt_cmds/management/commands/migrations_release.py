# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.loader import MigrationLoader
from django.core.files.base import ContentFile

from migrations_mgmt_cmds.storage import migrations_releases_storage


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

        result = json.dumps(leaf_migrations, sort_keys=True, indent=4, separators=(",", ": "))

        release_path = "{}.json".format(options["release"])

        file_object = ContentFile(bytes(result, "utf-8"), name=release_path)

        migrations_releases_storage.save(release_path, file_object)
