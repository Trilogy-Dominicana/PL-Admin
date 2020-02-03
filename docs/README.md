# PL/SQL Manager
[Change to English](../README.md)

Esta herramienta ha sido creada pensando en esas aplicaciones que contienen mucha logica dentro de la base de datos.

PL-Admin te ayuda en la clonación de tu esquema de base de datos principal, compilar código pl/sql en tiempo real, revisar errores de compilacion, revisar diferencias entre la base de datos y tu repositorio entre otras cosas.

### Clona el repositorio
```sh
git@gitlab.viva.com.do:anaiboa/plsql-manager.git
```

### Setup
Copia el fichero `.env.sample` y reemplaza los parametros que hay dentro
```sh
cp .env.sample .env
```

Crea un alia del comando
```sh
# Abre tu configuración de perfil (.bash_profile or .zshrc)
vim ~/.bash_profile

# Agrega la siguiente linea:
alias plqmin="docker container exec -ti pl-admin pladmin"

# Cierra el fichero de configuración y carga nuevamente
source ~/.bash_profile
```

### Construye el contenedor
```sh
docker-compose up -d --build
```

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

### Topics
- [Crear nuevo esquema](docs/new-shcema-es.md)
- [Cambios desde la bases de dato al respositorio local (WC), `db2wc`](docs/wc2db-es.md)
- [Cambiar el password del SYSDBA](docs/change-sys-password-es.md)

### ¡Importante!
- Los nombres de los archivos en el repositorio deben ser el mismo que en la base de datos.
- Despues de cada commit, PL-Admin ejecuta el comanndo `wc2db` para sincronizar git con la base de datos.
