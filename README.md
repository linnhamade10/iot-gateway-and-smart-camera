# IoT Gateway and Smart Camera System

Edge computing and IoT gateway system using Raspberry Pi, Flask, sensors, computer vision, and cloud-based AI services.

## Overview

This project was developed as part of the DT373B Systems Design for Internet of Things course at Kristianstad University. A Raspberry Pi was configured as an IoT gateway and edge device to provide remote monitoring and control through Flask-based REST APIs and a web interface. The system integrated GPIO devices, sensors, a USB camera, and Azure cloud services to enable event-driven operation, sensor data acquisition, image classification, and machine learning applications.

## Features

* Configured a Raspberry Pi as an IoT gateway and edge device.
* Implemented Flask-based REST APIs for remote monitoring and control.
* Developed a web interface for interacting with the system.
* Controlled LEDs and GPIO devices through the web interface.
* Implemented event-driven image capture using a USB camera.
* Collected and buffered sensor data before transmitting batches to Azure IoT Hub.
* Transmitted sensor measurements and decision events using JSON messages.
* Implemented image classification using Azure Custom Vision.
* Performed visitor access control based on image classification results.
* Acquired accelerometer and gyroscope data from an MPU6050 sensor over I²C.
* Generated labeled datasets for posture recognition and machine learning applications.
* Combined local edge processing with cloud-based AI services.

## System Architecture

The system consists of:

* End devices connected through GPIO and I²C interfaces.
* Raspberry Pi gateway running Flask and REST APIs.
* Web-based user interface for monitoring and control.
* USB camera for image acquisition.
* Azure IoT Hub for cloud communication.
* Azure Custom Vision for image classification.
* Event-driven monitoring and control.

## Technologies

* Python
* Raspberry Pi
* Flask
* HTML
* CSS
* JavaScript
* REST APIs
* GPIO
* I²C
* MPU6050
* JSON
* Edge Computing
* IoT Systems
* Azure IoT Hub
* Azure Custom Vision
* Computer Vision
* Machine Learning

## Tools

* Git
* GitHub
* Visual Studio Code

## Repository Structure

```text
.
├── app.py
├── camera_classifier.py
├── posture_data_collection.py
├── templates/
│   └── index.html
├── static/
│   └── visitor.jpg
├── README.md
└── .gitignore
```

## Course

Developed as part of:

**DT373B – Systems Design for Internet of Things**
Kristianstad University

## Collaboration

Developed at Kristianstad University as part of the Systems Design for Internet of Things course.

## Credentials

Sensitive credentials have been removed from this repository.
