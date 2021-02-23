# Design Implementation

> This content was copied from [Jc2k's](https://gist.github.com/Jc2k) gist [README.md](https://gist.github.com/Jc2k/bacff3105653f3b28e84#file-readme-md) file

- [Batching migrations](#batching-migrations)
- [Caveats](#caveats)
  * [When merges are involved, Django doesn't always revert migrations cleanly](#when-merges-are-involved--django-doesn-t-always-revert-migrations-cleanly)
  * [Reverting fails a lot](#reverting-fails-a-lot)

## Batching migrations

The idea here is that if you know which migrations were in version `2.0.3` of your project and which were in version `2.0.4` then `setA - setB` gives you the list of migrations you need to undo.

Django migrations give you a directed acyclic graph which describes how to get from the current database state to the target state. But there is no mechanism by which you can perform tasks like `revert all the migrations that just ran in the last deployment`.

Here is a quick recipe for batching Django migrations to allow you to do things like that.

Before you tag your project you do:

    django freeze 2.0.3

This generates a `json` file in which looks like this:

    {
      "app-a": "0001_initial",
      "app-b": "0002_add_a_field"
    }

It lists all the apps configured in your project and their most recent migration. It's stored in your project folder in a releases subdirectory. It should be added to your VCS.

With this process in place we now have a list of targets for each tag. To go from any future database state back to `2.0.3` we *simply* have to undo any migration that is not reference in the `json` file (or one of its dependencies).

And we have a command to do that:

    django rollback 2.0.3


## Caveats

### When merges are involved, Django doesn't always revert migrations cleanly

If in `2.0.3` you had migrations that looked like this:

    A -> B

In this example you could unapply `B` with:

    django migrate my_app A

Now you deploy 2.0.4 and that graph becomes:

    A - > B - > D
     \- > C -/

(Where `D` is a merge migration that depends on `B` and `C`).

Now in `2.0.3` our metadata says that `B` is the latest migration. So under the hood our migration engine is going to try something like:

    django migrate my_app B

You might hope that `C` and `D` are reverted, but only `D` is reverted.

It may be possible to generate a list of all applied migrations and a list of all migrations the `B` depends on and work out that `C` and `D` should be reverted, then use Django's migration planner to execute them in a safe order. This has not been tested yet.


### Reverting fails a lot

It's quite common to change the database level constraints - for example to suddenly allow `NULL` data. You'll almost certainly end up with data that doesn't satisfy this constraint. So any attempt to revert will fail. Similar problems existing when changing the size of a field.

So relying on this as a strategy for backing our changes is risky! More testing should be added.