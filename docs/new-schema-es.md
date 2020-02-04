## PL-Admin - Crear un nuevo esquema
[Chenge to english](new-schema.md)

Despues de haber completado el setup de la herramienta, usuarmente el siguiente paso es crear un nuevo esquema. 

Cuando se ejecuta el comando `pladmin newSchema` la herramienta toma el valor de la variable *DB_USER* y verifica si existe un usuario con este nombre, si el usuario existe entonces mostrará un mensaje en pantalla indicando se debe utilizar el flag -f o --force para para borrar el usuario y crearlo nuevamente. 

> Es importante saber qué al utilizar el indicador -f o --force `pl-admin` eliminará el esquema existente con todos sus objetos y creará uno nuevo basado en los objetos que existen en el repositorio local.

Comando
```sh
pladmin newSchema
```

Forzar la creación del esquema
```sh
pladmin newSchema --force
```
