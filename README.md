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
# Where going to be your PL/SQL source code? 
export PLSQL_PATH=</var/www/omega/app/omegapl/your_pl_path>
export GIT_NAME=<Your Name>
export GIT_EMAIL=<your@email.com>

# Your schema name
export DB_USER=<user>

# Your password
export DB_PASSWORD=<password>

# This information has to be provided by DBA Team
export DB_SERVICE_NAME=<service_name>
export DB_HOST=<host>
export DB_PORT=<oracle_port>
export DB_ADMIN_USER=<sysDBA_user>
export DB_ADMIN_PASSWORD=<sysDBA_password>
export DB_DEFAULT_TABLE_SPACE=<default_table_spache>
export DB_TEMP_TABLE_SPACE=<temp_table_space>

# Main schema is the name from the system going take the data. In Viva Case the main schema is OMEGA
export DB_MAIN_SCHEMA=<OMEGA>

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
