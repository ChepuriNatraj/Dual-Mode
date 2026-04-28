# Arduino Pendrive Environment (Agent Handoff)

This file is a dedicated handoff note so future agents use the correct external Arduino setup.

## Canonical Paths (validated on April 25, 2026)
- USB mount root: `/media/natraj/ARDUINO_USB`
- Arduino config root: `/media/natraj/ARDUINO_USB/arduino_esp32_env`
- Arduino data dir: `/media/natraj/ARDUINO_USB/arduino_esp32_env/data`
- Arduino CLI config: `/media/natraj/ARDUINO_USB/arduino_esp32_env/data/arduino-cli.yaml`
- Detected board port during test: `/dev/ttyUSB0`

## Verified Working Commands
```bash
export ARDUINO_DATA_DIR="/media/natraj/ARDUINO_USB/arduino_esp32_env/data"

arduino-cli core list --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
arduino-cli board list --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"

arduino-cli compile --fqbn esp32:esp32:esp32 \
  /home/natraj/file/src/robot_arm_hardware/firmware/tests/test_01_single_servo_direct \
  --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"

arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 \
  /home/natraj/file/src/robot_arm_hardware/firmware/tests/test_01_single_servo_direct \
  --config-file "$ARDUINO_DATA_DIR/arduino-cli.yaml"
```

## If Mount Name Changes
```bash
ls -la /media/natraj
find /media/natraj -maxdepth 3 -type d -iname '*arduino*'
```

Then replace `ARDUINO_USB` in the path exports with the detected mount folder.
