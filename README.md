# PL/SQL Manager
This tools has been created thinking on those apps that has to many logict into the database.
PL/SQL Manage provide you an ease way to clone a main schema, compile pl/sql code on realtime, check database errors, check diferences between repo and database, etc.

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

# Add you repo url
export PLSQL_URL_REPO='git@gitlab.viva.com.do:anaiboa/pl-sql.git'
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
