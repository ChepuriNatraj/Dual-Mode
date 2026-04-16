# ESP32 Hardware Setup Guide

To save local storage space, the ESP32 board manager packages, toolchains, and libraries have been explicitly configured to install and run from an external USB drive (Pendrive).

## Pendrive Configuration Path
**Mount Point:** `/media/natraj/UBUNTU 24_0/arduino_esp32_env`

All `arduino-cli` dependencies limit themselves strictly to this directory.

## 1. Environment Variable Setup
Before interacting with the ESP32 (compiling, installing libraries, or uploading), you **MUST** export the custom Arduino data directory to your current terminal session. If you don't do this, Arduino CLI will default to your laptop's internal hard drive (`~/.arduino15`).

```bash
export ARDUINO_DATA_DIR="/media/natraj/UBUNTU 24_0/arduino_esp32_env/data"
```

## 2. Installing Dependencies (One-Time Setup)
If you need to reproduce this setup on another drive:

```bash
export ARDUINO_DATA_DIR="/media/natraj/UBUNTU 24_0/arduino_esp32_env/data"
mkdir -p "$ARDUINO_DATA_DIR"

# Initialize config
arduino-cli config init --dest-dir "$ARDUINO_DATA_DIR"

# Add ESP32 Boards URL
arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"

# Install ESP32 Core
arduino-cli core update-index --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
arduino-cli core install esp32:esp32 --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```

## 3. Compiling the Firmware
Compile the ROS 2 hardware interface wrapper (or your custom PCA9685 servo test scripts):

```bash
export ARDUINO_DATA_DIR="/media/natraj/UBUNTU 24_0/arduino_esp32_env/data"

arduino-cli compile --fqbn esp32:esp32:esp32 /home/natraj/file/src/robot_arm_hardware/firmware/arm_firmware --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```

## 4. Uploading to ESP32
Ensure the ESP32 is plugged securely via USB (typically mounts to `/dev/ttyUSB0` or `/dev/ttyACM0`).

```bash
export ARDUINO_DATA_DIR="/media/natraj/UBUNTU 24_0/arduino_esp32_env/data"

arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 /home/natraj/file/src/robot_arm_hardware/firmware/arm_firmware --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```
