# PL/SQL Manager
[Cambiar a Español](docs/README.md)

This tools has been created thinking on those apps that has to many logic into the database.

PL-Amin provide you an easy way to clone a main schema, compile pl/sql code on realtime, check database errors, check diferences between repo and database, etc.

### Requirements
- Docker version ^19.03.1
- Git ^2.22.0
- docker-compose version ^1.25.2, build 698e2846

### Clone the repository
```sh
git@gitlab.viva.com.do:anaiboa/plsql-manager.git
```

### Setup
Copy .env.sample and replace the params with your own parameters
```sh
cp .env.sample .env
```

Create an alias the made the proccess more easier
```sh
# Open your profile config should be .bash_profile or .zshrc
vim ~/.bash_profile

# Enter this line:
alias pladmin="docker container exec -ti pl-admin pladmin"

# Close the file and source you new alias
source ~/.bash_profile
```

### Build the container
```sh
docker-compose up -d --build
```

### Synopsis
pladmin [`command`] [`options`]
- wc2db [--dry-run, --force]
- db2wc [--dry-run, --force, --merge]
- newSchema
- compile
- errors
- watch

### Essential Commands
`newSchema`: Create new schema taking values from env vars
```sh
pladmin newSchema
```

`wc2db`: Compare the differences between the last synchronized commit and the local repository and take those changes to the database
> - --dry-run: Show what would be removed, created, but do not actually remove anything
> - --force: Will no do any validation to export the objects.
```sh
# usage
pladmin wc2db [options]
```

`db2wc`: Look for objects that has been changed on the database and then export it to local repo.
> - --dry-run: Show what would be exported but do not actually do anything.
> - --force: Will no do any validation to export the objects.
> - --merge: Merge the object that you are exporting with the local file. 
```sh
# usage
pladmin wc2db [options]
```

`compile`: Look for invalid objects and try to compile it.
```sh
# usage
pladmin compile
```

`errors`: List all the errors in the schema.
```sh
# usage
pladmin errors
```

`watch`: Take the changes to the database in real time.
```sh
# usage
pladmin watch
```

### Topics
- [Creating a New Shcema](docs/new-shcema.md)
- [Export changes from your Database to Git (db2wc)](docs/db2wc.md)
- [Change SYS DBA Password](docs/change-sys-password.md)

### Important!
- The file name has to be the same of the object name.
- After each commit, PL-Admin excute `wc2db` command to sinchronize *git* with the database.
