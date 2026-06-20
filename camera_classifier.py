# Import Flask to create the web server
from flask import Flask, render_template, redirect, url_for

from gpiozero import LED

# Used to run cleanup code when program exits
import atexit

# Used to run terminal commands (webcam)
import subprocess

# Used for file paths and checking files
import os

# Used to send HTTP requests to Azure Custom Vision
import requests


# Create the Flask app
app = Flask(__name__)

GREEN_PIN = 17
RED_PIN = 27

# Create LED objects
green_led = LED(GREEN_PIN)
red_led = LED(RED_PIN)

# Make sure LEDs start OFF
green_led.off()
red_led.off()



# CAMERA / FILE SETTINGS
# Path where the snapshot image will be saved
SNAPSHOT_PATH = os.path.join("static", "visitor.jpg")


# Azure Custom Vision credentials removed
# Set these as environment variables before running the application
PREDICTION_URL = os.getenv("PREDICTION_URL")
PREDICTION_KEY = os.getenv("PREDICTION_KEY")

if PREDICTION_URL is None or PREDICTION_KEY is None:
    raise RuntimeError(
        "PREDICTION_URL and PREDICTION_KEY environment variables must be set."
    )
# Tags expected from Custom Vision
ALLOW_TAG = "allow"
DENY_TAG = "deny"

# Store the latest result to show on the webpage
latest_result = {
    "tag": None,
    "probability": None,
    "message": "No image captured yet."
}


# Turn off LEDs when program stops
def cleanup():
    try:
        green_led.off()
        red_led.off()
    except:
        pass

# Make sure cleanup runs on exit
atexit.register(cleanup)


# CUSTOM VISION REQUEST
def call_custom_vision(image_path):
    """
    Sends an image to Azure Custom Vision and
    returns the predicted tag and probability.
    """
    # Read image file as binary
    with open(image_path, "rb") as f:
        data = f.read()

    # HTTP headers required by Azure
    headers = {
        "Prediction-Key": PREDICTION_KEY,
        "Content-Type": "application/octet-stream"
    }

    # Send image to Azure Custom Vision
    response = requests.post(PREDICTION_URL, headers=headers, data=data)
    response.raise_for_status()

    # Get prediction results
    predictions = response.json().get("predictions", [])
    if not predictions:
        return None, None

    # Pick the prediction with the highest probability
    best = max(predictions, key=lambda p: p["probability"])
    return best["tagName"], best["probability"]


def apply_decision(tag, prob):
    """
    Turns LEDs on/off based on prediction result
    and updates the message shown on the webpage.
    """
    global latest_result

    if tag == ALLOW_TAG:
        green_led.on()
        red_led.off()
        msg = f"Visitor ALLOWED – prob={prob:.2%} (green LED ON)"

    elif tag == DENY_TAG:
        red_led.on()
        green_led.off()
        msg = f"Visitor DENIED – prob={prob:.2%} (red LED ON)"

    else:
        green_led.off()
        red_led.off()
        msg = f"Unknown prediction: {tag}"

    # Save result so Flask can display it
    latest_result = {
        "tag": tag,
        "probability": prob,
        "message": msg
    }


def take_and_classify_snapshot():
    """
    Takes a photo using the webcam and
    sends it to Custom Vision for classification.
    """
    # Make sure the static folder exists
    os.makedirs("static", exist_ok=True)

    # Command to take a picture with the webcam
    cmd = [
        "fswebcam",
        "-d", "/dev/video0",
        "-r", "1280x720",
        "--no-banner",
        SNAPSHOT_PATH
    ]

    # Run the webcam command
    subprocess.run(cmd, check=True)

    # Send the image to Azure and apply decision
    tag, prob = call_custom_vision(SNAPSHOT_PATH)
    apply_decision(tag, prob)



# FLASK ROUTES
@app.route("/")
def index():
    """
    Main page.
    Shows snapshot, decision message, and confidence.
    """
    return render_template(
        "index.html",
        message=latest_result["message"],
        tag=latest_result["tag"],
        probability=latest_result["probability"],
        snapshot_exists=os.path.exists(SNAPSHOT_PATH)
    )


@app.route("/snapshot")
def snapshot():
    """
    Takes a snapshot and runs Custom Vision.
    """
    try:
        take_and_classify_snapshot()
    except Exception as e:
        # Show error and turn red LED on if something fails
        latest_result["message"] = f"Error: {e}"
        red_led.on()
        green_led.off()

    # Go back to main page
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Start Flask web server
    app.run(host="0.0.0.0", port=5000, debug=False)
