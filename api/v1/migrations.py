from flask import Blueprint, jsonify, request
from pladmin.migrations import Migrations

migrations = Blueprint('api', __name__)
objMigrations = Migrations()

@migrations.route('/', methods=['GET'])
def getAllMigrations():
    
    listMigrations = objMigrations.listAllMigration()

    return jsonify({
        'all_migrations' : listMigrations
    })

@migrations.route('/', methods=['POST'])
def generateScript():
    data = request.form

    fileType = data.get('fileType')
    quantity = int(data.get('quantity'))
    basicPL  = data.get('basicPL')

    if not fileType in ('as', 'ds'):
        return jsonify({
            'error': 'you can only choose between these options (as, ds)'
        })
    
    response = objMigrations.createScript(
        fileType=fileType, quantity=quantity, basicPl=basicPL
    )

    return jsonify ({
        'message': 'script create', 
        'response': response
    }) 

@migrations.route('/execute/<scriptType>', methods=['POST'])
def executeMigrationsByType(scriptType):

    if not scriptType in ('as', 'ds'):
        return jsonify({
            'error': 'you can only choose between these options (as, ds)'
        })

    orderScript = objMigrations.checkPlaceScript()
    response = objMigrations.migrate(scriptType)

    return jsonify ({
       'response': response,
       'order_scripts' : orderScript,
       'status_code':200
    })

@migrations.route('/execute/all', methods=['POST'])
def executeAllMigrations():
    options = ['as', 'ds']

    response = [objMigrations.migrate(typeFile=opt) for opt in options]
    
    return jsonify({
        'message' :  response
    })

@migrations.route('/<name>', methods=['DELETE'])
def removeMigration(name):
    response = objMigrations.removeMigrations(name)

    return jsonify({
      'response' : response 
    })

@migrations.route('/<name>/<typeFile>', methods=['GET'])
def getMigration(name, typeFile):
    response = objMigrations.getMigration(migration=name,typeFile=typeFile)
    return response 
   