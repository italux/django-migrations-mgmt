# Welcome to Django Management Commands 👋

[![License: GNU General Public License v2.0](https://img.shields.io/github/license/italux/django-migrations-mgmt)](https://github.com/italux/django-migrations-mgmt/blob/master/LICENSE)
![Version](https://img.shields.io/github/v/tag/italux/django-migrations-mgmt)
![Python version](https://img.shields.io/pypi/pyversions/django-migrations-mgmt)
![PyPi version](https://img.shields.io/pypi/v/django-migrations-mgmt)
![PyPi downloads](https://img.shields.io/pypi/dm/django-migrations-mgmt)

> A Django management commands to help on migrations deployment rollbacks

  * [Getting Started](#getting-started)
    + [Prerequisites](#prerequisites)
    + [Install](#install)
    + [Usage](#usage)
  * [Important Notes](#important-notes)
    + [Known Issues](#known-issues)
    + [Recomendations & Tips](#recomendations--tips)
  * [Documentation](#documentation)
  * [Contributing](#contributing)
  * [License](#license)
  * [Show your support](#show-your-support)
  * [Author](#author)

## Getting Started

This is a [fork](https://gist.github.com/italux/1fe473c5d05da496e09a4d23b12857cf) of [Jc2k's](https://gist.github.com/Jc2k) [work](https://gist.github.com/Jc2k/bacff3105653f3b28e84), where I've made small fixes, build and distribuite as a pypi package

> The idea here is that if you know which migrations were in version 2.0.3 of your project and which were in version 2.0.4 then setA - setB gives you the list of migrations you need to undo. See [Design Implementation](docs/design_implementation.md) document.

### Prerequisites

- Python >= 3.7
- Django >= 2.2

### Install
```sh
pip install django-migrations-mgmt
```

### Usage

- Add to django `settings.py`
```python
INSTALLED_APPS = [
    ...
    'migrations_mgmt_cmds',
    ...
]
...
# Inform the class' path that handle storage's backend
MIGRATIONS_RELEASES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
...
```

- Create a migration release
```sh
python manage.py migrations_release --release v0.1
```
- Check the release JSON file in your storage backend
```sh
ls
v0.1.json
```
- Create a new migration
```sh
python manage.py makemigrations
Migrations for 'sample_app':
  sample_app/migrations/0002_choice.py
    - Create model Choice
```
- Execute pending migrations
```sh
python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sample_app, sessions
Running migrations:
  Applying sample_app.0002_choice... OK
```
- Rollback the last applied migration
```sh
python manage.py migrations_rollback --release v0.1
Operations to perform:
  Revert sample_app 0002_choice
Running migrations:
  Rendering model states... DONE
  Unapplying sample_app.0002_choice... OK
```
- Check applied migrations
```sh
python manage.py showmigrations
```

## Important Notes

### Storage's Backend

The storage's backend to be used can be informed passing a class' path to the setting `MIGRATIONS_RELEASES_STORAGE`, in case it isn't informed, the value set-up at Django's setting `DEFAULT_FILE_STORAGE` will be used instead.

You should inform the path as python package, e.g. `'path.Classname'`


#### Command `release_management`

This extension introduce a command to allow for displaying, disabling or deleting the release files available in the storage's backend: 

```
# Display list of ordered release files with extension .json
python manage.py release_management --display-list

# Display last created file with extension .json
python manage.py release_management --display-last

# Delete a file informed by path from storage
python manage.py release_management --delete-release=<file's path in storage>

# Rename a release file informed by path from storage, appending `.disabled` to its filename. 
python manage.py release_management --disable-release=<release file's path in storage>
```

### Known Issues

It's quite common to change the database level constraints - for example to suddenly allow NULL data - which you'll almost certainly end up with data that doesn't satisfy this constraint, and consequenctly any attempt to revert will fail. Similar problems existing when changing the size of a field.

So relying on this as a strategy for backing our changes is risky! More testing should be added.

### Recomendations & Tips

To avoid the rollback issues mentioned above please check the [Django Migrations Good Practices](docs/migrations_good_practices.md) documentation

## Documentation

- [Django Management Commands documentation](https://italux.github.io/django-migrations-mgmt/)

## Contributing

Contributions, issues and feature requests are welcome!

- Feel free to check [issues page](https://github.com/italux/django-migrations-mgmt/issues). 


## License

Copyright © 2021 [Italo Santos](https://github.com/italux).

This project is [GNU General Public License v2.0](https://github.com/italux/django-migrations-mgmt/blob/master/LICENSE) licensed.

## Show your support

Give a ⭐️ if this project helped you!

## Author

👤 **Italo Santos**

* Website: http://italosantos.com.br
* Twitter: [@italux](https://twitter.com/italux)
* Github: [@italux](https://github.com/italux)
* LinkedIn: [@italosantos](https://linkedin.com/in/italosantos)

***
_This README was generated with by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_
