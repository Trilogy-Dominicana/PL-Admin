## PL-Admin - Uso
[Change to english](usage.md)

### Synopsis
pladmin [`comando`] [`opciones`]
- wc2db [--dry-run, --force]
- db2wc [--dry-run, --force, --merge]
- newSchema
- watch
- compileSchema
- errors


### Lista de commandos
`newSchema`: Crea un nueva esquema tomando la configuración ingresada en el .env
```sh
pladmin newSchema
```

wc2db: Compara la diferencias entre la base de datos y el reposoririo local y reemplaza los objectos con diferencias dentro de la base de datos
> - --dry-run: Muestra todo lo que será creado, removido, etc. pero no ejecuta nada.
> - --force: Forza la sincronización del repositorio con la base de datos.

```sh
# uso
pladmin wc2db [opciones]
```

db2wc: Busca los objetos que tienen cambios en la base de datos y los exporta al respositorio local.
> - --dry-run: Muestra todo lo que será creado, removido, etc. pero no ejecuta nada.
> - --force: Forza la sincronización de la base de datos con el repositorio.
> - --merge: Hace un merge de los cambios en la base de datos y el repositorio local (beta). 
```sh
# uso
pladmin wc2db [opciones]
```

`compile`: Busca los objectos invalidos e intenta compilarlos.
```sh
# uso
pladmin compile
```

`watch`: Se mantiene escuchando cambios en el repositorio local y los lleva a la base de datos.
```sh
# uso
pladmin watch
```
