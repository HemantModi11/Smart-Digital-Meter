from flask import Blueprint, request, jsonify
import bcrypt
from database import users_collection, devices_collection, bills_collection, notifications_collection, thresholds_collection
from models import device_presets

app_routes = Blueprint("app_routes", __name__)

# User Registration
@app_routes.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data["email"]
    password = data["password"]

    if users_collection.find_one({"email": email}):
        return jsonify({"success": False, "message": "User already exists"}), 400

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_collection.insert_one({"email": email, "password": hashed_password.decode()})

    return jsonify({"success": True, "message": "User registered successfully"}), 201

# User Login
@app_routes.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    user = users_collection.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    return jsonify({"success": True, "message": "Login successful", "token": email}), 200  # Using email as token for now

# Dashboard data
@app_routes.route("/dashboard", methods=["GET"])
def dashboard():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400

    latest_bill = bills_collection.find_one({"email": email}, sort=[("date", -1)])
    devices = devices_collection.find({"email": email})
    total_usage = sum(device.get("power_usage", 0) for device in devices)
    latest_notification = notifications_collection.find_one({"email": email}, sort=[("timestamp", -1)])

    return jsonify({
        "current_usage": total_usage,
        "current_bill": latest_bill["amount"] if latest_bill else 0,
        "latest_notification": latest_notification["message"] if latest_notification else "No alerts"
    }), 200

@app_routes.route("/billing_history", methods=["GET"])
def billing_history():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400

    bills = list(bills_collection.find({"email": email}).sort("generated_at", -1))  # Sort newest first

    for bill in bills:
        bill["_id"] = str(bill["_id"])

    return jsonify(bills), 200

@app_routes.route("/pay_bill", methods=["POST"])
def pay_bill():
    data = request.json
    email = data["email"]
    month = data["month"]

    result = bills_collection.update_one(
        {"email": email, "month": month, "status": "Unpaid"},
        {"$set": {"status": "Paid"}}
    )

    if result.modified_count == 0:
        return jsonify({"success": False, "message": "No unpaid bill found for this month"}), 404

    return jsonify({"success": True, "message": "Bill paid successfully!"}), 200

# Notifications
@app_routes.route("/notifications", methods=["GET"])
def get_notifications():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400

    notifications = list(notifications_collection.find({"email": email}, {"_id": 0}))
    return jsonify(notifications), 200

@app_routes.route("/set_threshold", methods=["POST"])
def set_threshold():
    data = request.json
    email = data["email"]
    threshold = data["threshold"]

    if not isinstance(threshold, int) or threshold < 0:
        return jsonify({"message": "Threshold must be a positive integer"}), 400

    thresholds_collection.update_one(
        {"email": email},
        {"$set": {"threshold": threshold}},
        upsert=True
    )

    return jsonify({"message": "Threshold updated successfully!"}), 200

# Add Device
@app_routes.route("/add_device", methods=["POST"])
def add_device():
    data = request.json
    email = data["email"]
    device_name = data["device_name"]
    power_usage = data.get("power_usage", device_presets.get(device_name, 100))

    devices_collection.insert_one({
        "email": email,
        "device_name": device_name,
        "power_usage": power_usage
    })

    return jsonify({"success": True, "message": "Device added successfully!"}), 201

# Get User Devices
@app_routes.route("/user_devices", methods=["GET"])
def user_devices():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Email is required"}), 400

    devices = list(devices_collection.find({"email": email}, {"_id": 0}))
    return jsonify(devices), 200

@app_routes.route("/analysis", methods=["GET"])
def household_analysis():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Fetch bills for the user
    bills = list(bills_collection.find({"email": email}))
    if not bills:
        return jsonify({"message": "No billing data found."}), 404

    # Sort by generated date
    bills.sort(key=lambda b: b["generated_at"])

    monthly_trend = []
    total_units = 0
    total_paid = 0
    unpaid_bills = 0
    threshold_crosses = 0

    threshold_doc = thresholds_collection.find_one({"email": email})
    threshold = threshold_doc["threshold"] if threshold_doc else 300

    for bill in bills:
        month = bill["month"]
        units = round(bill["units"], 2)
        amount = round(bill["amount"], 2)
        status = bill["status"]

        monthly_trend.append({
            "month": month,
            "units": units,
            "amount": amount,
            "status": status
        })

        total_units += units
        if status == "Paid":
            total_paid += amount
        else:
            unpaid_bills += 1

        if units > threshold:
            threshold_crosses += 1

    devices = list(devices_collection.find({"email": email}))
    device_data = []
    for device in devices:
        device_data.append({
            "device_name": device["device_name"],
            "power_usage": device["power_usage"]
        })

    response = {
        "monthly_trend": monthly_trend,
        "summary": {
            "total_units": round(total_units, 2),
            "total_paid": round(total_paid, 2),
            "unpaid_bills": unpaid_bills,
            "threshold_crosses": threshold_crosses,
            "threshold": threshold
        },
        "devices": device_data
    }

    return jsonify(response), 200