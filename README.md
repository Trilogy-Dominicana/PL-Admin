# PL/SQL Manager
[Cambiar a Español](docs/README.md)

This tools has been created thinking on those apps that has to many logic into the database.

PL-Amin provide you an easy way to clone a main schema, compile pl/sql code on realtime, check database errors, check diferences between repo and database, etc.

### Requirements
- Docker version ^19.03.1
- Git ^2.22.0

### Clone the repository
```sh
git@gitlab.viva.com.do:anaiboa/plsql-manager.git
```

### Setup enviroments vars
1. Edit your bash profile file
```sh
# Using bash
vim ~/.bash_profile

# Using ZSH
vim ~/.zshrc
```

2. Now, add the fallowing vars to the config:
```sh
# Where going to be your PL/SQL source code? 
export PLSQL_PATH=</var/www/omega/app/omegapl/your_pl_path>
export DB_USER=<user> #Your schema name
export DB_PASSWORD=<password> #Your password
export GIT_NAME=<Your name>
export GIT_EMAIL=<your@email.com.do>

# This information has to be provided by DBA Team
export DB_SERVICE_NAME=<service_name>
export DB_HOST=<host>
export DB_PORT=<oracle_port>
export DB_ADMIN_USER=<sysDBA_user>
export DB_ADMIN_PASSWORD=<sysDBA_password>
export DB_DEFAULT_TABLE_SPACE=<default_table_spache>
export DB_TEMP_TABLE_SPACE=<temp_table_space>
export DB_MAIN_SCHEMA=<MAIN_SCHEMA> #Schema where the data is. In our case is OMEGA

# PL-Admin alias
alias plqmin="docker container exec -ti pl-admin pladmin"
```

3. Load the new config

### Build the container
```sh
docker-compose up -d --build
```

### SYNOPSIS
pladmin [`command`] [`options`]
- wc2db [--dry-run, --force]
- db2wc [--dry-run, --force, --merge]
- newSchema
- watch
- compileSchema
- errors


### ESSENTIAL COMMANDS
`newSchema`: Create new schema taking values from env vars
```sh
pladmin newSchema
```

wc2db: compare the differences between the last synchronized commit and the local repository and take those changes to the database
> - --dry-run: Show what would be removed, created, but do not actually remove anything
> - --force: Will no do any validation to export the objects.
```sh
# usage
pladmin wc2db [options]
```

db2wc: Look for objects that has been changed on the database and then export it to local repo.
> - --dry-run: Show what would be exported but do not actually do anything.
> - --force: Will no do any validation to export the objects.
> - --merge: Merge the object that you are exporting with the local file. 
```sh
# usage
pladmin wc2db [options]
```

`compile`: Look for invalid packages and try to compile it.
```sh
# Inside of container 
pladmin compile
```

`watch`: Take the changes to the database in real time.
```sh
# Inside of container 
pladmin watch
```


### Topics
- [Change SYSDBA Password](docs/change-sys-password.md)
