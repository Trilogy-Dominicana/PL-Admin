## PL-Admin - Cambiar contraseña de SYSDBA o cualquier otro parametro
[Change to Spanish](change-sys-password-es.md)

Si tu necesitas cambiar la contraseña de tu esquema, administración, esquema principal o cualquier otro parametro, lo único que debes hacer es modificar las variables de entorno en el archivo .bash_profile o .zshrc que se encuentra en tu home. 


Abre tu archico de configurción
```sh
# Bash
vim ~/.bash_profile

# ZSH
vim ~/.zshrc
```

Ejecuta el comando source para aplicar los cambios.
```sh
soruce ~/.zshrc
```

Reinicia el ambiente.
```sh
docker-compose restart
```

Revisa que todo esté correcto.
```sh
# docker exec -ti pl-admin echo <env_var>, ejemplo:
docker exec -ti pl-admin echo $DB_ADMIN_PASSWORD
```

Si no se aplicó el cambio, recrea la imagen y el contenedor.
```sh
docker-compose up -d --build
```
