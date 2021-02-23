# Django Migrations Good Practices

* [Basic rules](#basic-rules)
* [Fake migration](#fake-migration)
  + [When to fake](#when-to-fake)
* [Related articles](#related-articles)

## Basic rules

1. **Add new fields as nullable** \
Having a nullable field allows backward compatibility while partial deploy is in progress.

2. **Don’t add default values for existing tables** \
The migration will try to add default values for all existing entries in the table, a good recipe for a timeout.

3. **Unset the index for new ForeignKey on an existing model** \
By default, ForeignKeys are indexed, which will lead to a lock and constraint change in the database, probably resulting in a timeout. If really necessary, try on off-hours.

4. **Attention to the migration number before merging** \
Remember, we are a big team, so your migration number might become outdated by the time you merge.

5. **Add raw SQL to the Pull Request description.** \
The command `python manage.py sqlmigrate [app_name] [migration_id]` is very useful to check the SQL commands of your migration and add the output to the pull request will give more context to reviewers

## Fake migration

[Fake a migration](https://docs.djangoproject.com/en/2.2/ref/django-admin/#cmdoption-migrate-fake) is the process to update the Django model without actually running the SQL to change your database schema.

This process should be done only in specifics scenarios

### When to fake

1. **Do not "physically" remove fields or models (i.e.: tables or columns)** \
To avoid data loss, and also keep backward compatibility run these migrations as `--fake` will make Django unlink the database references, but the data will still be there in case it is needed.

2. **Change related_name only** \
Related names are only a Django trick, not really part of the database schema, so running a `--fake` is safe. That is needed because there is a bug in Django that changing related names triggers a constraint change, which, again, will lead to a timeout. See bug [#25253](https://code.djangoproject.com/ticket/25253)

## Related articles

[Keeping Django database migrations backward compatible](https://medium.com/3yourmind/keeping-django-database-migrations-backward-compatible-727820260dbb)