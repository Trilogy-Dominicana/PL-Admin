SELECT
    owner
     , OBJECT_ID
    , object_name
    , object_type
    , status
    , last_ddl_time
    , created
FROM all_objects WHERE owner= 'WDELACRUZ3' AND status = 'INVALID' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');


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



