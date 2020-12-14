class utils:
    def dryRun():
        print(
            """
 _____  _______     __     _____  _    _ _   _ 
|  __ \|  __ \ \   / /    |  __ \| |  | | \ | |
| |  | | |__) \ \_/ /_____| |__) | |  | |  \| |
| |  | |  _  / \   /______|  _  /| |  | | . ` |
| |__| | | \ \  | |       | | \ \| |__| | |\  |
|_____/|_|  \_\ |_|       |_|  \_\\_____/|_| \_| 
-----------------------------------------------
         No change will take effect.
-----------------------------------------------\n """
        )

    def getObjectDictInList(objects, name, type):
        """ Get an spesific object from a list of dicts"""
        data = dict(
            filter(
                lambda objDB: (
                    objDB["object_name"] == name and objDB["object_type"] == type
                ),
                objects.items(),
            )
        )

        return data


    def getObjectDict(objects, name, type):
        """ Get an spesific object from a list of dicts and return a dict"""

        data = next(
            (
                item
                for item in objects
                if item["object_name"] == name and item["object_type"] == type
            ),
            None,
        )

        return data

    # def filterScript(objects, name, type):
    #     """ Get an spesific object from a list of dicts and return a dict"""

    #     data = next(
    #         (
    #             item
    #             for item in objects
    #             if item["object_name"] == name and item["object_type"] == type
    #         ),
    #         None,
    #     )

    #     return data


    def scriptExample():
            return """-------------------------------------------------------------
-- ESTO ES UN ARCHIVO GENERADO AUTOMATICAMENTE POR PLADMIN
-------------------------------------------------------------

-------------------------------------------------------------
-- NO OLVIDES PONER AL MENOS UN DBMS_OUTPUT.PUT_LINE
-------------------------------------------------------------
-- DBMS_OUTPUT.PUT_LINE("Script ejecutado correctamente");

-------------------------------------------------------------
-- ESPESIFICA EL ESQUEMA EN CADA SENTENCIA
-------------------------------------------------------------
-- UPDATE SCHEMA.TABLE_NAME WHERE TALCOSA=0;

-------------------------------------------------------------
-- HACER COMMIT EN LOS DML
-------------------------------------------------------------
-- COMMIT;

"""
