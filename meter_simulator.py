import schedule
import time
import random
from datetime import datetime, timedelta
from database import devices_collection, bills_collection, users_collection, notifications_collection, thresholds_collection
from utils import send_email

ELECTRICITY_RATE = 7

virtual_date = datetime(2025, 1, 1)

def calculate_consumption():
    global virtual_date
    month = virtual_date.strftime("%B")
    year = virtual_date.year

    print(f"📅 Simulated Month: {month} {year}")

    users = users_collection.find()

    for user in users:
        email = user["email"]
        devices = devices_collection.find({"email": email})

        total_units = 0
        for device in devices:
            power = device["power_usage"]
            name = device["device_name"].lower()

            # Determine hours used based on appliance type
            if "ac" in name or "air conditioner" in name:
                hours_used = random.randint(4, 10)  # AC typically used 4-10 hours/day
            elif "light" in name or "bulb" in name or "lamp" in name:
                hours_used = random.randint(4, 7)  # Lights typically 4-7 hours/day
            elif "refrigerator" in name or "fridge" in name:
                hours_used = 24  # Fridge runs continuously but cycles on/off
            elif "tv" in name or "television" in name:
                hours_used = random.randint(2, 6)  # TV typically 2-6 hours/day
            elif "washing machine" in name or "washer" in name:
                hours_used = random.uniform(0.5, 1.5)  # Used for 1-2 loads/day
            elif "water heater" in name or "geyser" in name:
                hours_used = random.uniform(1, 3)  # Heater runs 1-3 hours/day
            elif "microwave" in name or "oven" in name:
                hours_used = random.uniform(0.25, 1)  # Used for short periods
            elif "computer" in name or "laptop" in name or "pc" in name:
                hours_used = random.randint(2, 8)  # Computers used 2-8 hours/day
            elif "fan" in name or "ceiling fan" in name:
                hours_used = random.randint(8, 12)  # Fans often run most of the day
            elif "dishwasher" in name:
                hours_used = random.uniform(0.5, 1.5)  # Runs for 1-2 cycles/day
            elif "router" in name or "modem" in name:
                hours_used = 24  # Runs continuously
            elif "iron" in name or "clothes iron" in name:
                hours_used = random.uniform(0.25, 0.75)  # Used for short periods
            elif "vacuum" in name or "cleaner" in name:
                hours_used = random.uniform(0.25, 1)  # Used for short cleaning sessions
            elif "toaster" in name:
                hours_used = random.uniform(0.1, 0.25)
            elif "blender" in name or "mixer" in name:
                hours_used = random.uniform(0.1, 0.3)
            else:
                hours_used = random.randint(1, 3)  # Default for unspecified devices

            daily_kWh = (power * hours_used) / 1000
            total_units += daily_kWh

        monthly_units = round(total_units * 30, 2)
        bill_amount = round(monthly_units * ELECTRICITY_RATE, 2)

        threshold_doc = thresholds_collection.find_one({"email": email})
        threshold_limit = threshold_doc["threshold"] if threshold_doc else 300

        # Notifications
        if monthly_units > threshold_limit:
            message = f"You have exceeded your threshold limit of {threshold_limit} units!"
            notifications_collection.insert_one({
                "email": email,
                "message": message,
                "type": "Alert",
                "timestamp": time.time(),
                "month": month,
                "year": year
            })
            send_email(email, "Usage Alert", message)

        elif monthly_units > (threshold_limit * 0.8):
            message = f"Your electricity usage is reaching the threshold of {threshold_limit} units. Consider saving power."
            notifications_collection.insert_one({
                "email": email,
                "message": message,
                "type": "Warning",
                "timestamp": time.time(),
                "month": month,
                "year": year
            })
            send_email(email, "Usage Warning", message)

        elif monthly_units < 250:
            message = f"Great job! Your consumption this month is just {monthly_units} units. Keep saving energy!"
            notifications_collection.insert_one({
                "email": email,
                "message": message,
                "type": "Info",
                "timestamp": time.time(),
                "month": month,
                "year": year
            })

        # Bill creation or update
        existing_bill = bills_collection.find_one({"email": email, "month": month, "year": year})
        if not existing_bill:
            bills_collection.insert_one({
                "email": email,
                "units": monthly_units,
                "amount": bill_amount,
                "status": "Unpaid",
                "month": month,
                "year": year,
                "generated_at": datetime.now()
            })
            send_email(email, "Monthly Electricity Bill", f"Your bill for {month} is ₹{bill_amount:.2f} for {monthly_units} kWh.")
        else:
            bills_collection.update_one(
                {"_id": existing_bill["_id"]},
                {"$set": {"units": monthly_units, "amount": bill_amount, "generated_at": datetime.now()}}
            )

        unpaid = bills_collection.find_one({"email": email, "status": "Unpaid", "month": {"$ne": month}})
        if unpaid:
            notifications_collection.insert_one({
                "email": email,
                "message": f"You have a pending electricity bill of ₹{unpaid['amount']} from {unpaid['month']}. Please pay it soon.",
                "type": "Reminder",
                "timestamp": time.time(),
                "month": month,
                "year": year
            })
            send_email(email, "Pending Bill Reminder", f"You have a pending bill of ₹{unpaid['amount']} from {unpaid['month']}.")

    virtual_date = virtual_date + timedelta(days=30)

schedule.every(1).minutes.do(calculate_consumption)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)