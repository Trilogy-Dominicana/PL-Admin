## PL-Admin - Creating a new shcema
[Cambiar a Español](new-schema-es.md)

When the newSchema command is executed, pl-admin takes the value in the variable `DB_USER` creates the schema and then creates all the objects that are in the local repository.

If the schema already exists, the tool will give a choice that it cannot continue and the -f or --force option should be used.

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
