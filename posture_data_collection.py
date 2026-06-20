# Used to communicate with I2C devices (MPU6050 sensor)
import smbus

# Used for timing and delays
import time

# Used to save data into a CSV file
import csv

# Used to add date and time to the filename
from datetime import datetime


# MPU6050 REGISTER ADDRESSES

# I2C address of the MPU6050 sensor
MPU_ADDR = 0x68

# Power management register (used to wake the sensor)
PWR_MGMT_1 = 0x6B

# Starting register for accelerometer data
ACCEL_XOUT_H = 0x3B

# Starting register for gyroscope data
GYRO_XOUT_H = 0x43

# I2C BUS SETUP

# Use I2C bus 1 (default on Raspberry Pi)
bus = smbus.SMBus(1)

# Wake up the MPU6050 (it starts in sleep mode)
bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)


def read_word(reg):
    """
    Reads two bytes from the sensor and converts them
    into a signed 16-bit value.
    """
    high = bus.read_byte_data(MPU_ADDR, reg)        # High byte
    low = bus.read_byte_data(MPU_ADDR, reg + 1)     # Low byte

    # Combine high and low bytes
    value = (high << 8) + low

    # Convert to signed value if needed
    if value >= 0x8000:
        value = -((65535 - value) + 1)

    return value


def read_accel():
    """
    Reads accelerometer data (x, y, z) in g units.
    """
    ax = read_word(ACCEL_XOUT_H) / 16384.0
    ay = read_word(ACCEL_XOUT_H + 2) / 16384.0
    az = read_word(ACCEL_XOUT_H + 4) / 16384.0
    return ax, ay, az


def read_gyro():
    """
    Reads gyroscope data (x, y, z) in degrees per second.
    """
    gx = read_word(GYRO_XOUT_H) / 131.0
    gy = read_word(GYRO_XOUT_H + 2) / 131.0
    gz = read_word(GYRO_XOUT_H + 4) / 131.0
    return gx, gy, gz


# USER INPUT

print("Posture data collection")
print("Labels: 0 = Sitting, 1 = Standing, 2 = Fast Walking")

# Ask user to choose posture label
label = input("Enter posture label (0/1/2): ").strip()


# FILE SETUP


# Create filename with label and timestamp
filename = f"posture_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

print("Recording for 60 seconds at 50 Hz...")
print("Do NOT change posture during recording.")


# DATA RECORDING LOOP

# Open CSV file for writing
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)

    # Write header row
    writer.writerow([
        "timestamp",
        "ax", "ay", "az",
        "gx", "gy", "gz",
        "label"
    ])

    start_time = time.time()

    # Record data for 60 seconds
    while time.time() - start_time < 60:
        timestamp = time.time()

        # Read sensor values
        ax, ay, az = read_accel()
        gx, gy, gz = read_gyro()

        # Save one row of data
        writer.writerow([
            timestamp,
            ax, ay, az,
            gx, gy, gz,
            label
        ])

        # Wait 0.02 seconds (50 samples per second)
        time.sleep(0.02)



print(f"Data saved to {filename}")
print("Done.")
