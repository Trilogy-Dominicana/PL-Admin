from flask import Flask, jsonify, request

app = Flask(__name__)

# from api.v1.routes import mode
from api.v1.migrations import migrations

# app.register_blueprint(mode, url_prefix='/api/v1')
app.register_blueprint(migrations, url_prefix='/api/v1/migrations/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000, debug=True)