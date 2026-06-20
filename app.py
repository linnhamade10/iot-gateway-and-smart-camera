# Flask is used to create a web server and web API
from flask import Flask, render_template, jsonify, request

from gpiozero import LED, Button

# atexit lets us run cleanup code when the program stops
import atexit

# json is used to convert Python data into JSON format
import json

# subprocess lets us run Linux terminal commands (for the webcam)
import subprocess

from datetime import datetime

# Azure IoT libraries for sending data to the cloud
from azure.iot.device import IoTHubDeviceClient, Message

import os

# Azure IoT Hub connection string removed
# Replace with your own connection string 
CONNECTION_STRING = "YOUR_CONNECTION_STRING"

# Create a client that connects this Raspberry Pi to Azure IoT Hub
iot_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

# Print a message so we know the connection worked
print("Connected to Azure IoT Hub")


# FLASK WEB APPLICATION SETUP
# Create the Flask application
app = Flask(__name__)

# "access allowed"
green_led = LED(17)

# "access denied"
red_led = LED(27)

# Turn both LEDs off when the program starts
green_led.off()
red_led.off()

# Physical button connected to GPIO pin 22
# pin is HIGH until the button is pressed
doorbell = Button(22, pull_up=True)


# PHONE SENSOR DATA BUFFER
# List that temporarily stores sensor data sent from a phone
sensor_buffer = []

# Number of samples to collect before sending to Azure
BATCH_SIZE = 20



# FUNCTION: SEND SENSOR DATA TO AZURE
def send_batch_to_cloud(batch):
    """
    Sends a batch of phone sensor data to Azure IoT Hub.
    """
    try:
        # Create a dictionary that will become JSON data
        payload = {
            "source": "phone_gateway",                  # Who sent the data
            "timestamp": datetime.utcnow().isoformat() + "Z",  # Current time
            "sampleCount": len(batch),                  # Number of samples
            "samples": batch                             # Actual sensor data
        }

        # Convert the dictionary to a JSON message
        msg = Message(json.dumps(payload))

        # Tell Azure this is JSON text
        msg.content_encoding = "utf-8"
        msg.content_type = "application/json"

        # Send the message to Azure IoT Hub
        iot_client.send_message(msg)
        print("Sent sensor batch to Azure:", payload)

    except Exception as e:
        # Print error if sending fails
        print("Error sending batch to Azure:", e)


def send_decision_to_cloud(decision):
    """
    Sends an allow or deny decision to Azure IoT Hub.
    """
    try:
        # Create decision message
        payload = {
            "source": "door_gateway",                   # Door system
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision": decision                         # allow or deny
        }

        # Convert dictionary to JSON message
        msg = Message(json.dumps(payload))
        msg.content_encoding = "utf-8"
        msg.content_type = "application/json"

        # Send the decision to Azure
        iot_client.send_message(msg)

        print("Sent decision to Azure:", payload)

    except Exception as e:
        print("Error sending decision to Azure:", e)


# FUNCTION: TAKE A SNAPSHOT WITH WEBCAM
def take_snapshot():
    """
    Takes a photo using a USB webcam and saves it as visitor.jpg.
    """
    try:
        # Run the fswebcam command using Linux
        result = subprocess.run(
            [
                "fswebcam",           # Webcam program
                "-d", "/dev/video0",  # Webcam device
                "-r", "1280x720",     # Image resolution
                "--no-banner",        # No text on image
                "static/visitor.jpg" # File save location
            ],
            capture_output=True,
            text=True,
        )

        # Print command output (for debugging)
        print("Snapshot stdout:", result.stdout)
        print("Snapshot stderr:", result.stderr)

        return True

    except Exception as e:
        print("Snapshot error:", e)
        return False



# FUNCTION: WHAT HAPPENS WHEN DOORBELL IS PRESSED
def doorbell_pressed():
    """
    This function runs automatically when the doorbell is pressed.
    """
    print("Doorbell pressed taking snapshot...")

    # Take a photo when someone presses the doorbell
    if take_snapshot():
        print("Snapshot taken from doorbell press.")


# Tell the button to run doorbell_pressed() when pressed
doorbell.when_pressed = doorbell_pressed

def cleanup():
    """
    Releases hardware resources and closes Azure connection.
    """
    # Release GPIO pins
    green_led.close()
    red_led.close()
    doorbell.close()

    # Safely shut down Azure client
    try:
        iot_client.shutdown()
    except Exception:
        pass


# Register cleanup function to run automatically on exit
atexit.register(cleanup)


# FLASK ROUTES (WEB API)
@app.route("/")
def home():
    """
    Loads the main web page.
    """
    return render_template("index.html")


@app.route("/led/<color>/<state>")
def control_led(color, state):
    """
    Turns LEDs on or off through a web request.
    Example: /led/green/on
    """
    if color == "green":
        led = green_led
    elif color == "red":
        led = red_led
    else:
        return jsonify({"status": "error", "message": "Unknown LED color"}), 400

    if state == "on":
        led.on()
    elif state == "off":
        led.off()
    else:
        return jsonify({"status": "error", "message": "Unknown state"}), 400

    return jsonify({"status": "success", "color": color, "state": state})


@app.route("/sensor", methods=["POST"])
def sensor_data():
    """
    Receives sensor data from a phone.
    Sends it to Azure once 20 samples are collected.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    samples = data.get("samples")
    if not isinstance(samples, list) or len(samples) == 0:
        return jsonify({"status": "error", "message": "No samples list"}), 400

    # Add samples to buffer
    for s in samples:
        sensor_buffer.append(s)

    print(f"Received {len(samples)} samples. Buffer size now {len(sensor_buffer)}")

    # Send to Azure when buffer is full
    if len(sensor_buffer) >= BATCH_SIZE:
        batch = sensor_buffer.copy()
        sensor_buffer.clear()
        send_batch_to_cloud(batch)

    return jsonify({"status": "ok", "bufferSize": len(sensor_buffer)})


@app.route("/snapshot")
def snapshot_route():
    """
    Takes a snapshot when triggered from the website.
    """
    if take_snapshot():
        return jsonify({"status": "ok", "message": "Snapshot captured"})
    else:
        return jsonify({"status": "error", "message": "Snapshot failed"}), 500


@app.route("/decision/<action>", methods=["POST"])
def decision(action):
    """
    Handles allow or deny decision from the website.
    """
    if action == "allow":
        green_led.on()
        red_led.off()
    elif action == "deny":
        red_led.on()
        green_led.off()
    else:
        return jsonify({"status": "error", "message": "Unknown action"}), 400

    # Send decision to Azure
    send_decision_to_cloud(action)

    return jsonify({"status": "ok", "decision": action})


# START THE PROGRAM
if __name__ == "__main__":
    try:
        # Start Flask web server
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        # Make sure hardware is cleaned up
        cleanup()
