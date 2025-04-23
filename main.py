from flask import Flask
from flask_cors import CORS
from routes import app_routes
import threading
import schedule
import time
from meter_simulator import calculate_consumption  # make this a function in the module

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(app_routes, url_prefix="/api")

def run_scheduler():
    schedule.every(1).minutes.do(calculate_consumption)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Run the scheduler in the background
    t = threading.Thread(target=run_scheduler)
    t.start()

    # Start the Flask server
    app.run(host="0.0.0.0", port=5000)