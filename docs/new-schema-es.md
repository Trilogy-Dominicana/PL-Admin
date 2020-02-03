## PL-Admin - Crear un nuevo esquema
[Chenge to english](new-schema.md)

Cuando se ejecuta el comando newSchema, pl-admin toma el valor en la variable `DB_USER` crea el esquema y entonces crea todos los objetos que se encuentran en el respositorio local.

Si el esquema ya existe, la herramienta dará una elerta de que no puede continuar y se deberá utilizar la opción -f o --force. 

> It is important to know that using the -f or --force pl-admin flag will delete the existing schema with all its objects and create a new one based on the objects that exist in the local repository.

```sh
pladmin newShcema <options>
```

```sh
pladmin newShcema -f
```
