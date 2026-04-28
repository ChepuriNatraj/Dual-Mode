#!/usr/bin/env bash
# Source this file before Arduino compile/upload steps.
export ARDUINO_DATA_DIR="/media/natraj/ARDUINO_USB/arduino_esp32_env/data"
export ARDUINO_CONFIG_FILE="$ARDUINO_DATA_DIR/arduino-cli.yaml"
echo "ARDUINO_DATA_DIR=$ARDUINO_DATA_DIR"
echo "ARDUINO_CONFIG_FILE=$ARDUINO_CONFIG_FILE"
