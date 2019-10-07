SELECT
    owner
     , OBJECT_ID
    , object_name
    , object_type
    , status
    , last_ddl_time
    , created
FROM all_objects WHERE status = 'INVALID' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');

SELECT * FROM all_objects WHERE status = 'INVALID' AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');

SELECT distinct object_type FROM all_objects ;
                                --AND object_type in ('PACKAGE','FUNCTION','PROCEDURE', 'VIEW');

SELECT distinct status FROM all_objects;


select * from all_errors where owner = 'EBRADMIN';

