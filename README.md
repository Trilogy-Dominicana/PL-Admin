# PL/SQL Manager
[Cambiar a Español](docs/README.md)

This tools has been created thinking on those apps that has to many logic into the database.

PL-Amin provide you an easy way to clone a main schema, compile pl/sql code on realtime, check database errors, check diferences between repo and database, etc.

### Requirements
- Docker version ^19.03.1

### Setup
Clone the repo
```sh
git clone git@gitlab.viva.com.do:anaiboa/pl-admin.git
```

Creating images and container
```sh
# Build the docker image
docker build --no-cache -t viva/pl-admin .

# Create the container
docker run -ti --name=pladmin-omega -d -v <path/to/plsql_code>:/plsql viva/pl-admin

# In case that you have other schema just create another container with other name
docker run -ti --name=pladmin-reclamaciones -d -v <path/to/plsql_code>:/plsql viva/pl-admin
```

Copy .env.sample file to each pl/sql path and change the params
```sh
cp .env.sample you_plsql_path/.env
``

Create an alias the made the proccess more easier
```sh
# Open your profile config should be .bash_profile or .zshrc
vim ~/.bash_profile

# Enter this line:
alias pladmin="docker container exec -ti pladmin-omega pladmin"

# If you have multiple schemas, enter this line too:
alias pl-reclamaciones="docker container exec -ti pladmin-reclamaciones pladmin"

# Close the file and source you new alias
source ~/.bash_profile
```

### Topics
- [Usage](docs/usage.md)
- [Creating a New Shcema](docs/new-schema.md)
- [Export changes from your Database to Git (db2wc)](docs/db2wc.md)
- [Change SYS DBA Password](docs/change-sys-password.md)

### Important!
- The file name has to be the same of the object name.
- Do not duplicate files
- The file extension indicate what kind of object is:
    - PACKAGE: `.psk`
    - PACKAGE BODY: `.pbk`
    - VIEW: `.vew`
    - FUNCTION: `.fnc`
    - PROCEDURE: `.prc`
