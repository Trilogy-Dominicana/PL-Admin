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
            return """           
/* STANDARD PARA LOS SCRIPTS A EJECUTAR VIA ESTA HERRAMIENTA: 
 - SE DEBE ESPECIFICAR EL SCHEMA EN CADA SENTENCIA (EJ. UPDATE SCHEMA.TABLE_NAME WHERE...).
 - PONER DBMS_OUTPUT EN CADA INSTRUCCION DEL SCRIPT.
 - PONER MANEJO DE EXCEPCIONES EN CADA INSTRUCCION DEL SCRIPT. 
 - EL FLUJO DE EJECUCION NORMAL DEL SCRIPT, DEBE IMPONER QUE SI EJECUTA "SIN CAER" EN NINGUNA EXCEPCION, A PARTE DE LOS OUTPUTS "PARCIALES" (QUE CORRESPONDEN A CADA PASO DEL SCRIPT), SE INCLUYA    -- TAMBIEN UN OUTPUT FINAL DEL SCRIPT CON EL SIGUIENTE TEXTO: 'Script completado satisfactoriamente'(RECORDAR UTILIZAR COMILLAS SIMPLES);
 - MANEJO DE COMMIT:
    - SI EL DESARROLLADOR CONSIDERA MEJOR COMMIT PARA CADA INSTRUCCION DEL SCRIPT, ASI COMO UN SOLO COMMIT AL FINAL DEL SCRIPT, FAVOR CONSIDERAR PARA LOS DBMS_OUTPUT Y MANEJO DE EXCEPCIONES.
 - EN OPERACIONES DE BULK DML, HACER COMMIT MAXIMO CADA 50,000 REGISTROS.
 - SI EL SCRIPT VA A UTILIZAR CURSORES NO IMPLICITOS, RECORDAR QUE HAY QUE CERRAR EL CURSOR DESPUES DE UTILIZARLO (HABER HECHO FETCH DEL CURSOR); RECORDAR QUE LOS CURSORES IMPLICITOS SON LOS ASOCIADOS A LAS OPERACIONES DE DML (INSERT, DELETE Y UPDATE) EXCLUSIVAMENTE.
 - SI EL SCRIPT VA A HACER PROCESO DE ETL (EJ. TRUNCATE DE UNA TABLA VIA EXECUTE IMMEDIATE), CONSIDERAR LO SIGUIENTE:
    - SI LA TABLA SE VA A REPOBLAR CON UNA CANTIDAD DE DATOS DENTRO DE UN +-10% A LA CANTIDAD DE INFORMACION QUE HABIA AL MOMENTO DE EFECTUAR EL TRUNCADO DE LA MISMA, UTILIZAR LA CLAUSULA REUSE STORAGE (EJ. TRUNCATE TABLE NOMBRE_TABLA REUSE STORAGE);
    - SI LA TABLA SE VA A REPOBLAR CON UNA CANTIDAD DE DATOS FUERA DE UN +-10% A LA CANTIDAD DE INFORMACION QUE HABIA AL MOMENTO DE EFECTUAR EL TRUNCADO DE LA MISMA, UTILIZAR LA CLAUSULA DROP STORAGE (EJ. TRUNCATE TABLE NOMBRE_TABLA DROP STORAGE);
*/

"""
