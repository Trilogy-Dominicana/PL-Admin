class utils:
    def dryRun(self):
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
-----------------------------------------------\n 
            """
        )

    def getObjectDictInList(self, objects, name, type):
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


    def getObjectDict(self, objects, name, type):
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
