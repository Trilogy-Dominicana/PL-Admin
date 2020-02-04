## PL-Admin - Creating a new schema
[Cambiar a español](new-schema-es.md)

After completing the tool setup, the next step is to create a new scheme.

When the `pladmin newSchema` command is executed, the tool takes the value of the variable *DB_USER* and verifies if exist a user with this name, if the user exists then it will show a message on the screen indicating the flag -f or --force to delete the user and create it again.

> It is important to know that using the -f or --force pl-admin flag will delete the existing schema with all its objects and create a new one based on the objects that exist in the local repository.

Usage
```sh
pladmin newSchema
```

Force schema creation
```sh
pladmin newSchema --force
```
