from flask import Flask
from flask_cors import CORS
from routes import app_routes

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(app_routes, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True)