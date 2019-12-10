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

    def getObjectDict(objects, name, type):
        """ Get an spesific object from a list of dicts"""
        data = list(filter(
            lambda objDB: (
                objDB["object_name"] == name and objDB["object_type"] == type
            ),
            objects,
        ))

        return data
