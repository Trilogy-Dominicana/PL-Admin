-- Validate if the user exists
SELECT COUNT(1) AS v_count FROM dba_users WHERE username = UPPER('wdelacruz')


-- Create the user
CREATE USER wdelacruz IDENTIFIED BY passwrd1 DEFAULT TABLESPACE OMEGA_DATA TEMPORARY TABLESPACE TEMP_TBS QUOTA UNLIMITED ON OMEGA_DATA;


-- Give permissión (*GRANT ALL)
GRANT CREATE PROCEDURE TO wdelacruz;
GRANT CREATE SEQUENCE TO wdelacruz;
GRANT CREATE TABLE TO wdelacruz;
GRANT CREATE VIEW TO wdelacruz;
GRANT CREATE TRIGGER TO wdelacruz;
GRANT EXECUTE ANY PROCEDURE TO wdelacruz;
GRANT SELECT ANY DICTIONARY TO wdelacruz;
GRANT CREATE SESSION TO wdelacruz;
GRANT CREATE SYNONYM TO wdelacruz;
--GRANT CREATE SNAPSHOT TO wdelacruz;
--GRANT EXECUTE ON dbms_lock TO wdelacruz;
--GRANT CREATE DATABASE LINK TO wdelacruz;
--GRANT UPDATE ON sys.source$ TO wdelacruz;



-- Update Synonyms
SELECT oo.object_name, oo.object_type, oo.status
  FROM sys.dba_objects oo
 WHERE     oo.owner = 'OMEGA'
       AND oo.object_type IN ('SEQUENCE', 'TABLE', 'TYPE')
       AND oo.object_name NOT LIKE 'SYS_PLSQL_%%'
       AND oo.object_name NOT LIKE 'QTSF_CHAIN_%%'
       AND oo.object_name <> 'METADATA_TABLE'
       AND NOT EXISTS
              (SELECT 1
                 FROM sys.dba_objects tob
                WHERE     tob.owner = 'WDELACRUZ'
                      AND tob.object_name = oo.object_name)
       AND status = 'VALID';



CREATE SYNONYM WDELACRUZ.ACCOUT_SUBSCRIBER_SUSP FOR OMEGA.ACCOUT_SUBSCRIBER_SUSP;
CREATE SYNONYM WDELACRUZ.ACTOR_SEQ FOR OMEGA.ACTOR_SEQ;
CREATE SYNONYM WDELACRUZ.LISTTABLE FOR OMEGA.LISTTABLE;
CREATE SYNONYM ACCOUT_SUBSCRIBER_SUSP FOR WDELACRUZ2.ACCOUT_SUBSCRIBER_SUSP



# Create Grants

SELECT oo.object_name, oo.object_type, oo.status
from sys.dba_objects oo
where oo.owner=:target_schema
      and oo.object_type in ('SEQUENCE','TABLE','TYPE')
      and oo.object_name not like 'SYS_PLSQL_%%'
      and oo.object_name not like 'QTSF_CHAIN_%%'
      and oo.status='VALID'
      and oo.object_name not in (SELECT tp.table_name from dba_tab_privs tp where tp.grantee=:target_user and owner=:target_schema)


