# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.functional import LazyObject
from django.core.files.storage import get_storage_class


__all__ = ["migrations_releases_storage"]


class MigrationsReleasesStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class(
            getattr(settings, "MIGRATIONS_RELEASES_STORAGE", settings.DEFAULT_FILE_STORAGE)
        )()


migrations_releases_storage = MigrationsReleasesStorage()
