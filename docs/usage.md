## PL-Admin - Usages
[Cambiar a español](usage-es.md)

### Synopsis
[`**alias_name**`] [`command`] [`options`]
- wc2db [--dry-run, --force]
- db2wc [--dry-run, --force]
- newSchema
- compile
- errors
- watch

### Essential Commands
`newSchema`: Create new schema taking values from env vars
```sh
pladmin newSchema
```

`wc2db`: Compare the differences between the last synchronized commit and the local repository and take those changes to the database
> - --dry-run: Show what would be removed, created, but do not actually remove anything
> - --force: Will no do any validation to export the objects.
```sh
# usage 
pladmin wc2db [options]
```

`db2wc`: Look for objects that has been changed on the database and then export it to local repo.
> - --dry-run: Show what would be exported but do not actually do anything.
> - --force: Will no do any validation to export the objects.
> - --merge: Merge the object that you are exporting with the local file. 
```sh
# usage
pladmin wc2db [options]
```

`compile`: Look for invalid objects and try to compile it.
```sh
# usage
pladmin compile
```

`errors`: List all the errors in the schema.
```sh
# usage
pladmin errors
```

`watch`: Take the changes to the database in real time.
```sh
# usage
pladmin watch
```
