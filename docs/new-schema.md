## PL-Admin - Creating a new shcema
[Cambiar a Español](new-schema-es.md)

When the newSchema command is executed, pl-admin takes the value in the variable `DB_USER` creates the schema and then creates all the objects that are in the local repository.

If the schema already exists, the tool will give a choice that it cannot continue and the -f or --force option should be used.


```sh
pladmin newShcema <options>
```

```sh
pladmin newShcema -f
```
