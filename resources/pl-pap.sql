SELECT
    owner
    , OBJECT_ID
    , object_name
    , object_type
    , status
    , last_ddl_time
    , created
FROM dba_objects WHERE owner= 'WDELACRUZ3' AND status = 'INVALID' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');


SELECT
    owner
     , OBJECT_ID
    , object_name
    , object_type
    , status
    , last_ddl_time
    , created
FROM dba_objects WHERE owner = 'WDELACRUZ3' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');



SELECT * FROM all_objects WHERE status = 'INVALID' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');


SELECT distinct object_type FROM all_objects;
                             --AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');

SELECT distinct status FROM all_objects;


select * from dba_errors where owner = 'WDELACRUZ3'
AND name = 'TX_VDA_JOBS';
-- group by name;


select * from
-- Vista de dependencias de un paquete.
select * from all_dependencies;

select * from dba_users;


ALTER PACKAGE BODY WDELACRUZ3.TX_PTO_ENTREGAPUNTO COMPILE


--datetime.now().strftime("%Y%m%d%H%M%S")

SELECT
    object_id
    ,object_name
    ,object_type
    ,status
    ,last_ddl_time
FROM dba_objects 
where owner = 'WDELACRUZ1'
and object_name = 'TX_PRT_PROCESO';

ALTER PACKAGE WDELACRUZ3.TX_PRT_PROCESO COMPILE;


SELECT 
--     count(1) as total
    dbs.owner
    ,dbs.object_name
    ,dbs.object_type
    ,dbs.status
    ,dbs.last_ddl_time
    ,mt.last_ddl_time as mlast_ddl_time
    ,mt.object_path
    ,mt.last_commit
FROM dba_objects dbs
INNER JOIN WDELACRUZ1.PLADMIN_METADATA mt on dbs.object_name = mt.object_name and dbs.object_type = mt.object_type
WHERE dbs.owner = 'WDELACRUZ1'
AND dbs.LAST_DDL_TIME <> mt.LAST_DDL_TIME
AND dbs.object_type in ('PACKAGE', 'VIEW', 'FUNCTION', 'PR OCEDURE', 'PACKAGE BODY');

