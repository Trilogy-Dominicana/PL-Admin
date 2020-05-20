# PL/SQL Manager
[Change to English](../README.md)

Esta herramienta ha sido creada pensando en esas aplicaciones que contienen mucha logica dentro de la base de datos.

PL-Admin te ayuda en la clonación de tu esquema de base de datos principal, compilar código pl/sql en tiempo real, revisar errores de compilacion, revisar diferencias entre la base de datos y tu repositorio entre otras cosas.

### Setup
Clone the repo
```sh
git clone git@github.com:Trilogy-Dominicana/PL-Admin.git
```

## docker-compose example
```yml
version: "3.7"
services:
  pladmin-omega:
    image: viva/pl-admin
    container_name: pladmin-omega
    build:
      context: '.'
    volumes:
      - <you_plsql_path>:/plsql # <-- NO OLVIDES REEMPLAZAR <you_plsql_path> POR EL PATH DE TU CÓDIGO PL/SQL
    tty: true
    networks:
      - backend
```

Creating images and container
```sh
# Construir la imagen con la aplicación
docker build --no-cache -t viva/pl-admin .

# Crear el contenedor para un esquema
docker run -ti --name=pladmin-omega -d -v <path/to/plsql_code>:/plsql viva/pl-admin

# En caso de que tengas más de un esquema, siemplemente crea otro contenedor con nombre diferente
docker run -ti --name=pladmin-reclamaciones -d -v <path/to/plsql_code>:/plsql viva/pl-admin
```

Copia el fichero .env.sample a cada ruta donde tengas código pl/sql
```sh
cp .env.sample you_plsql_path/.env
``

Crea un alias para que sea más fácil ejecutar el comando
```sh
# Abre la configuración de tu perfil. puede ser .bash_profile o .zshrc dependiendo del shell que estes utilizando
vim ~/.bash_profile

# Agrega esta linea:
alias pladmin="docker container exec -ti pladmin-omega pladmin"

# En caso de que tengas más de un esquema, repite el mismo paso cambiando el nombre del contenedor
alias pl-reclamaciones="docker container exec -ti pladmin-reclamaciones pladmin"

# Cierra el fichero y no olvides cargar la configuración que ingresaste
source ~/.bash_profile
```


### Topics
- [Uso](usage-es.md)
- [Crear nuevo esquema](new-schema-es.md)
- [Exportar desde la base de datos al respositorio local (db2wc)](docs/db2wc-es.md)
- [Cambiar el password del SYSDBA](change-sys-password-es.md)

> ### ¡Importante para el repositorio del código PL/SQL!
> - Los nombres de los archivos deben ser el mismo que el nombre del objeto.
> - No pueden haber archivos duplicados en el albort de directorios.
> - Las extensiones de cada archivo determinará que tipo de objecto es.
> - Cada objecto debe estar dentro del directorio correspondiente.

| Objecto | Extención | Ruta |
| ------ | ------ | ------ |
| PACKAGE | .pks | ./packages |
| PACKAGE BODY | .pks | ./packages |
| VIEW | .vw | ./views |
| FUNCTION | .fnc | ./functions |
| PROCEDURE | .prc | ./procedures |
