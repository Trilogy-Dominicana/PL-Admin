# PL/SQL Manager
This tools has been created thinking on those apps that has to many logic into the database.
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
```

### Build the container
```sh
docker-compose up -d --build
```

### Options Available

`Create Schema`: Creating new schema. This option take the config and all you files in a current branch y create new schema
```sh
# Inside of container 
pladmin newSchema
    
#  Outside of container
docker -exec -ti pl-admin pladmin newSchema
```


`Update Schema`: This command compare the changes between master remote branch and current files chaange on your local working directory and replace it in you current schema
```sh
# Inside of container 
pladmin updateSchema

# Outside of container
docker -exec -ti pl-admin pladmin updateSchema
```


`Watcher`: Take the changes to the database in real time.
```sh
# Inside of container 
pladmin watch

# Outside of container
docker -exec -ti pl-admin pladmin watch
```


`Compile Invalids`: Look for invalid packages and try to compile it. 
```sh
# Inside of container 
pladmin compileInvalids

# Outside of container
docker -exec -ti pl-admin pladmin compileInvalids
```


`Working copy to DB`: Take all objects that you have in you working copy and override it into database.
```sh
# Inside of container 
pladmin wc2db

# Outside of container
docker -exec -ti pl-admin pladmin wc2db
```

`DB to Working copy`: Takes changes objects that you have in you working copy and override it into database.
```sh
# Inside of container 
pladmin db2wc

# Outside of container
docker -exec -ti pl-admin pladmin db2wc
```
