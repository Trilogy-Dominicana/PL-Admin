# PL/SQL Manager
This tools has been created thinking on those apps that has to many logict into the database.
PL/SQL Manage provide you an ease way to clone a main schema, compile pl/sql code on realtime, check database errors, check diferences between repo and database, etc.

We rely on the git standard and assume that your master branch is the main branch, that means the all operations with respect to changes are evaluated starting from the master branch

### Requirements
- Docker version ^19.03.1
- Git ^2.22.0

### Clone the repository
```sh
git@gitlab.viva.com.do:anaiboa/plsql-manager.git
```

### Define enviroment vars
```sh
# Where goin to be your PL/SQL source code? 
export PLSQL_PATH=</var/www/your_pl_path>

# - DB_SERVICE_NAME='DIAOMEGA'
# - DB_HOST='maisi.om.do'
# - DB_USER='WDELACRUZ4'
# - DB_PASSWORD='temp'
# - DB_PORT=1521
# - DB_ADMIN_USER='sys'
# - DB_ADMIN_PASSWORD='infinityqx35'
# - DB_DEFAULT_TABLE_SPACE='OMEGA_DATA'
# - DB_TEMP_TABLE_SPACE='TEMP_TBS'
# - DB_MAIN_SCHEMA='OMEGA'

```

### Build the container
```sh
docker-compose up -d --build
```

### Commands available
```sh
# Create schema
pladmin newSchema

# Check Database errors
pladmin checkErrors

# Update schema (You must excecute after avery git pull, merge o branch changed)
pladmin updateSchema
```
