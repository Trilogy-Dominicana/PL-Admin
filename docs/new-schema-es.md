## PL-Admin - Crear un nuevo esquema
[Chenge to english](new-schema.md)

If you need change the admin password, schema name, main schema or another params you have modify the enviroments vars saved on .bash_profile or .zshrc file depending of the shell that you are using.


Open you config file
```sh
# Bash
vim ~/.bash_profile

# ZSH
vim ~/.zshrc
```

Source the params
```sh
soruce ~/.zshrc
```

Restart the container
```sh
docker-compose restart
```

Check if everything is ok
```sh
# docker exec -ti pl-admin echo <env_var> e.g:
docker exec -ti pl-admin echo $DB_ADMIN_PASSWORD
```

If this no work for you, just rebuild the image and the container
```sh
docker-compose up -d --build
```
