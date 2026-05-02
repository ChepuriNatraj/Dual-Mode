# ESP32-CAM Complete Setup Guide - Step by Step

> **First Time Setup - Follow exactly as written**

**Estimated Time:** 15-20 minutes  
**Difficulty:** Beginner-Friendly

---

## 📋 What You'll Do

1. ✅ Connect ESP32-CAM via USB
2. ✅ Check current firmware using Serial Monitor
3. ✅ Prepare Arduino IDE with your pendrive packages
4. ✅ Create/Upload MJPEG streaming code
5. ✅ Verify it works by accessing video stream
6. ✅ Configure IP in ROS launch file

---

## 🔌 Step 1: Hardware Connection

### Connect ESP32-CAM to Your Linux Machine:

```
┌─────────────────────────────────────┐
│ USB Power Adapter (5V, 500mA+)      │
└────────────────────┬────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │      ESP32-CAM Module  │
        │                        │
        │ (Has USB Port)         │
        └────────────────────────┘
                     │
                     ↓
        Linux Machine (USB Port)
```

**What to connect:**
- USB cable from **USB-to-Serial adapter** to ESP32-CAM's USB port
- Power USB to your Linux machine

### Verify Connection:

```bash
# Check if the device appeared:
lsusb | grep "USB"
# Look for something like "CP2102" or "CH340"

# Also check serial ports:
ls -la /dev/ttyUSB* /dev/ttyACM*
# Should see at least one device (e.g., /dev/ttyUSB0)
```

**If you see it, continue. If not, check USB cable connection and try a different port.**

---

## 🖥️ Step 2: Check Current ESP32 Firmware (Serial Monitor)

First, let's see **what's currently on the ESP32**:

```bash
# Install minicom if not already present:
sudo apt-get install -y minicom

# Connect to ESP32 at 115200 baud:
minicom -D /dev/ttyUSB0 -b 115200
```

### What to Look For:

When ESP32 boots, you'll see messages like:
```
ets Jun  8 2016 00:22:57 rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_BOOT)
ets_main.c:371: vTaskStartScheduler
E (355) spi_flash: Trying to read iol_pins efuse with vdd set to 1800 when max expected value is 1100
```

**Possible outcomes:**

✅ **Good Sign:** You see boot logs (means hardware is OK)  
❌ **Bad Sign:** Nothing appears (check USB cable, baud rate, or port)  
❌ **Garbled text:** Wrong baud rate (try 9600, 74880, 115200)

### Exit minicom:
Press `Ctrl+A` then `Q` then `Y`

---

## 🛠️ Step 3: Prepare Arduino IDE

### Option A: Use System Arduino IDE (EASY)

If you have Arduino IDE installed on your machine:

```bash
# Check if Arduino is installed:
which arduino

# If yes, install ESP32 boards:
# Settings > Additional Boards Manager URLs > Add this:
# https://dl.espressif.com/dl/package_esp32_index.json

# Then: Tools > Board Manager > Search "esp32" > Install
```

### Option B: Use Arduino CLI with Your Pendrive (RECOMMENDED)

Your pendrive has pre-downloaded packages. Use Arduino CLI:

```bash
# Install Arduino CLI:
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Move to PATH:
sudo mv ~/bin/arduino-cli /usr/local/bin/

# Verify:
arduino-cli version
```

Create a config file pointing to your pendrive:

```bash
# Create config directory:
mkdir -p ~/.arduino15

# Create boards.local.txt pointing to your pendrive:
cat > ~/.arduino15/arduino-cli.yaml << 'EOF'
directories:
  data: /media/natraj/ARDUINO_USB/arduino_data
  downloads: /media/natraj/ARDUINO_USB/arduino_data/staging
  user: /home/natraj/Arduino
runtimes:
  - platform: linux64
    archive: {}
EOF
```

Test the config:

```bash
# List available boards:
arduino-cli board listall | grep esp32

# You should see:
# esp32:esp32:esp32           ESP32 Dev Module
# esp32:esp32:esp32cam        ESP32-CAM module
```

---

## 📝 Step 4: Create & Upload MJPEG Streaming Code

### Create the Sketch File:

```bash
# Create working directory:
mkdir -p ~/Arduino/esp32_camera_stream
cd ~/Arduino/esp32_camera_stream

# Create the sketch:
cat > esp32_camera_stream.ino << 'EOFSKETCH'
/*
  ESP32-CAM MJPEG Streaming Server
  This code streams video from ESP32-CAM via HTTP MJPEG
  Streams on port 81: http://IP:81/stream
*/

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// CAMERA_MODEL_AI_THINKER is for the standard esp32-cam module
#define CAMERA_MODEL_AI_THINKER

#include "camera_pins.h"

// WiFi Credentials - CHANGE THESE TO YOUR NETWORK
const char* ssid = "YOUR_SSID";           // ← CHANGE THIS
const char* password = "YOUR_PASSWORD";   // ← CHANGE THIS

WebServer server(80);

// Camera frame buffer
static esp_err_t init_camera()
{
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;    // 640x480
  config.jpeg_quality = 10;
  config.fb_count = 2;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return err;
  }

  return ESP_OK;
}

// MJPEG streaming handler
static esp_err_t stream_handler(httpd_req_t *req)
{
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char * part_buf[64];
  static int64_t last_frame = 0;
  if(!last_frame) {
    last_frame = esp_timer_get_time();
  }

  res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=123456789000000000000987654321");
  if(res != ESP_OK){
    return res;
  }

  while(true){
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
    } else {
      _jpg_buf_len = fb->len;
      _jpg_buf = fb->buf;
    }

    if(res == ESP_OK){
      size_t hlen = snprintf((char *)part_buf, 64, "Content-Length: %u\r\nContent-Type: image/jpeg\r\n\r\n", _jpg_buf_len);
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
    }
    if(res == ESP_OK){
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }
    if(res == ESP_OK){
      res = httpd_resp_send_chunk(req, "\r\n--123456789000000000000987654321\r\n", 38);
    }
    if(fb){
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if(_jpg_buf){
      free(_jpg_buf);
      _jpg_buf = NULL;
    }
    if(res != ESP_OK){
      break;
    }
    int64_t frame_time = esp_timer_get_time() - last_frame;
    last_frame = esp_timer_get_time();
    if(frame_time > 0)
    {
      Serial.printf("FPS: %0.1f\n", 1000000.0 / (uint32_t)frame_time);
    }
  }

  return res;
}

// Simple status endpoint
void handleRoot() {
  String html = "<h1>ESP32-CAM Streaming Server</h1>";
  html += "<p><a href='/stream'>View Stream (http://";
  html += WiFi.localIP().toString();
  html += ":81/stream)</a></p>";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\nStarting ESP32-CAM...");

  // Initialize LED flash if available
  pinMode(4, OUTPUT); // Usually GPIO4 is the LED

  // Initialize WiFi
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  int timeout = 20; // 20 second timeout
  while (WiFi.status() != WL_CONNECTED && timeout > 0) {
    delay(500);
    Serial.print(".");
    timeout--;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection FAILED - Check SSID and password");
  }

  // Initialize camera
  Serial.println("Initializing camera...");
  if(init_camera() != ESP_OK) {
    Serial.println("Camera init Failed! Check pin assignments and camera.pins.h");
    return;
  }
  Serial.println("Camera initialized successfully");

  // Set up HTTP server
  server.on("/", handleRoot);
  server.begin();
  Serial.println("HTTP server started");
  Serial.print("Stream available at: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
}

void loop() {
  server.handleClient();
  delay(1);
}
EOFSKETCH

echo "✅ Sketch created at ~/Arduino/esp32_camera_stream/esp32_camera_stream.ino"
```

### Get Camera Pins Definition:

```bash
# Download the camera pins header:
curl -o ~/Arduino/esp32_camera_stream/camera_pins.h \
  https://raw.githubusercontent.com/espressif/esp32-camera/master/camera_pins.h

echo "✅ Camera pins header downloaded"
```

---

## 🔧 Step 5: Edit WiFi Credentials

**This is CRITICAL - the code won't connect without correct WiFi credentials:**

```bash
# Open the sketch in your favorite editor:
nano ~/Arduino/esp32_camera_stream/esp32_camera_stream.ino

# Find these lines (around line 20):
# const char* ssid = "YOUR_SSID";
# const char* password = "YOUR_PASSWORD";

# Replace with YOUR actual WiFi network:
# const char* ssid = "MyHomeWiFi";           // ← Your WiFi name
# const char* password = "MyPassword123";    // ← Your WiFi password

# Save: Ctrl+X, then Y, then Enter
```

---

## 📤 Step 6: Upload Code to ESP32-CAM

### Put ESP32-CAM into Programming Mode:

This is **IMPORTANT** - you must do this before uploading:

```
┌─────────────────────────────────┐
│     ESP32-CAM Top View          │
├─────────────────────────────────┤
│                                 │
│  ┌──────────┐                   │
│  │  Camera  │                   │
│  │  Sensor  │                   │
│  └──────────┘                   │
│                                 │
│  [GPIO0] ← IMPORTANT!           │
│  [GND]   ← IMPORTANT!           │
│                                 │
│  Jumper GND here:       ┐       │
│  (or use wire)          │       │
│                         ↓       │
│  Connect GPIO0 ————→ GND pin    │
│                                 │
└─────────────────────────────────┘
```

**STEPS:**
1. **Disconnect USB** from ESP32
2. Using a **wire or jumper cable**, connect **GPIO0 pin to GND pin**
3. **Reconnect USB** - now it's in Programming Mode
4. You should see `esp32 download mode` in serial monitor

### Upload Using Arduino CLI:

```bash
cd ~/Arduino/esp32_camera_stream

# Compile the sketch:
arduino-cli compile --fqbn esp32:esp32:esp32cam \
  --libraries-dir /media/natraj/ARDUINO_USB/arduino_data/libraries \
  .

# Expected output:
# Sketch uses X bytes of program storage space
# Global variables use Y bytes of dynamic memory

# Upload to board:
arduino-cli upload --fqbn esp32:esp32:esp32cam \
  -p /dev/ttyUSB0 \
  --libraries-dir /media/natraj/ARDUINO_USB/arduino_data/libraries \
  .

# Watch for:
# Uploading...
# ...............................................Done uploading
```

**If upload fails:**
- ❌ "Device not found" → Check GPIO0 still connected to GND
- ❌ "Permission denied /dev/ttyUSB0" → Run: `sudo usermod -a -G dialout $USER` (then logout/login)
- ❌ "esptool.py not found" → Install: `pip install esptool`

---

## 🔌 Step 7: Boot and Check IP Address

Once upload completes:

1. **Disconnect the GPIO0-GND wire**
2. **Reset the board** (press RST button or unplug/replug USB)
3. **Watch serial monitor** for boot logs:

```bash
minicom -D /dev/ttyUSB0 -b 115200
```

**You should see:**
```
Starting ESP32-CAM...
Connecting to WiFi: MyHomeWiFi
....
WiFi connected!
IP address: 192.168.1.XX  ← ⭐ WRITE THIS DOWN
Camera initialized successfully
HTTP server started
Stream available at: http://192.168.1.XX:81/stream
```

**Copy the IP address - you'll need this!**

Exit minicom: `Ctrl+A` then `Q` then `Y`

---

## ✅ Step 8: Test Camera Stream

From your Linux machine, test if the stream works:

```bash
# Replace with YOUR IP from Step 7:
IP="192.168.1.XX"

# Method 1: Open in Firefox/Chrome:
firefox http://$IP:81/stream

# You should see LIVE VIDEO STREAM from the camera!

# Method 2: Test with curl:
curl -v http://$IP:81/stream | head -c 1000
# Should show MJPEG binary data (looks like gibberish - that's correct!)
```

**If you see video: 🎉 SUCCESS!**  
**If it times out: Check WiFi connection, GPIO0 disconnected, Serial monitor logs**

---

## 🚀 Step 9: Configure ROS Launch File

Now that you have the IP, update your ROS launch file:

```bash
cd ~/file && source install/setup.bash

# Launch autonomous sorting with YOUR camera IP:
ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://192.168.1.XX:81/stream
```

**Replace `192.168.1.XX` with YOUR actual IP from Step 7**

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"No module named 'camera_pins'"** | Run Step 4 to download camera_pins.h |
| **Upload says "timed out waiting for packet header"** | GPIO0 must be connected to GND during upload |
| **WiFi connect fails** | Check SSID/password spelling; WiFi must be 2.4GHz (not 5GHz) |
| **Can't access http://IP:81/stream** | Check both devices on same network; try ping first |
| **Nothing in serial monitor** | Wrong baud rate; try 74880 or 9600 |
| **Camera stream works but ROS doesn't connect** | Try: `timeout 30 ros2 run robot_arm_vision esp32_camera_bridge` |

---

## 📋 Quick Reference Card

**Bookmark this for future use:**

```
ESP32-CAM WiFi IP:           192.168.1.XX    (from Step 7)
WiFi SSID:                   MyHomeWiFi
Stream URL:                  http://192.168.1.XX:81/stream
Serial Port:                 /dev/ttyUSB0
Baud Rate:                   115200
Board Type:                  esp32:esp32:esp32cam
Arduino CLI Config:          ~/.arduino15/arduino-cli.yaml
Pendrive Packages Location:  /media/natraj/ARDUINO_USB/arduino_data
```

---

**NEXT STEP:** Run the upload command in Step 6 and watch for success! Report back with the IP address once you see it in the serial monitor.

