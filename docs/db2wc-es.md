## PL-Admin - Exportar cambios desde la base de datos a Git (db2wc)
[Change to english](wc2db-es.md)

Con PL-Admin puedes hacer tus cambios dentro de la base de datos y posteriormente exportarlos al respositorio local.

El proceso es simple, despues de haber creado tu esquema solo debes empezar a trabajar en la base de datos, una vez todo listo, solo debes ejecutar el comando `pladmin wc2db` para extraer los cambios desde la base de datos al respositorio indicado en la variable de configuración `PLSQL_PATH`.

Es importante saber que PL-Admin no hace commit por nosotros, una vez ejecutado el comando `pladmin db2wc` debemos verificar los cambios y hacer commit. Si no se hace commit al ejecutar nuevamente el commando `pladmin db2wc` la herramienta dará una alerta indicando que hay cambios pentiendes y se deberá utilizar el flag -f o --force para porder ejecutar exportar los cambios desde la base de datos al repositorio.


Ejecutar el proceso y no hace ningun cambio
```sh
pladmin db2wc --dry-run
```
> Al utilizar `--dry-run` estás indicando a PL-Admin que ejecute todo el proceso pero que no aplique ningún cambio. Esta opción es utilizada para ver que pasará si ejecutas dicho comando


Uso
```sh 
pladmin db2wc
```

Para forzar la exportación: 
```sh
pladmin db2wc --force
```
> Al utilizar --force estás indicando a PL-Admin que exporte los cambios desde la base de datos al repositorio sin importar si este tiene modificaciones locales. 



