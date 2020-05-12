# PL-admin scripts

## Structure migrations
- /plsql/scripts/DDL/year/month/day
- /plsql/scripts/DML/year/month/day

## Synopsis
pladmin [`command`] [`options`]
- make [--s=ddl, -s=dml]
- migrate [--s=ddl, -s=dml]

## Commands 
`make`: Create new script
```sh
pladmin make -s=ddl
pladmin make -s=dml
```
`migrate`: execute all pending migrations according to type (ddl, dml)
```sh
pladmin migrate -s=ddl
pladmin migrate -s=dml
```