# ESP32-CAM Flashing - Quick Action Checklist

> **Follow these steps IN ORDER - don't skip any**

---

## ✅ STEP 1: Physical Hardware Setup (5 minutes)

### Check Hardware:

```bash
# Verify USB device is connected:
lsusb | grep "FT232"
# Should see: Future Technology Devices International, Ltd FT232 Serial

ls -la /dev/ttyUSB0
# Should show: crw-rw---- 1 root dialout
```

### Physical Connections on ESP32-CAM:

```
USB Cable from FT232 to ESP32-CAM
ESP32-CAM has these pins:
- 3V3 (power)
- GND (ground) 
- TX (transmit)
- RX (receive)
- RESET
- GPIO0 ← IMPORTANT FOR PROGRAMMING

For now, just keep it powered and connected
```

**ACTION:** Plug in USB cable, verify with `lsusb`

---

## ✅ STEP 2: Check Serial Connection (2 minutes)

### Install minicom:

```bash
sudo apt-get update && sudo apt-get install -y minicom
```

### Connect to ESP32:

```bash
# Open serial monitor:
minicom -D /dev/ttyUSB0 -b 115200

# You should see BOOT logs like:
# ets Jun  8 2016 00:22:57 rst:0x1 (POWERON_RESET)
# E (355) spi_flash: ...
# (Don't worry about the error messages - they're normal)

# If you see logs: ✅ Hardware is working!
# If nothing: ❌ Check USB cable, or try baud rate 74880
```

**Exit minicom:** Press `Ctrl+A`, then `Q`, then `Y`

**ACTION:** Verify you can see boot logs, then exit

---

## ✅ STEP 3: Create Arduino Sketch (3 minutes)

### Create the sketch file:

```bash
# Create folder:
mkdir -p ~/Arduino/esp32_camera_stream
cd ~/Arduino/esp32_camera_stream

# Download the complete sketch:
cat > esp32_camera_stream.ino << 'EOF'
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// ========== CHANGE THESE LINES ==========
const char* ssid = "YOUR_WIFI_NAME";        // ← YOUR WiFi network name
const char* password = "YOUR_WIFI_PASSWORD"; // ← YOUR WiFi password
// =======================================

WebServer server(80);

static esp_err_t init_camera() {
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
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 10;
  config.fb_count = 2;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return err;
  }
  return ESP_OK;
}

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;

  httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=123456789000000000000987654321");

  while(true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
      break;
    }

    _jpg_buf_len = fb->len;
    _jpg_buf = fb->buf;

    char part_buf[64];
    size_t hlen = snprintf(part_buf, 64, "Content-Length: %u\r\nContent-Type: image/jpeg\r\n\r\n", _jpg_buf_len);
    
    res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
    if(res != ESP_OK) break;
    
    res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    if(res != ESP_OK) break;
    
    res = httpd_resp_send_chunk(req, "\r\n--123456789000000000000987654321\r\n", 38);
    if(res != ESP_OK) break;

    esp_camera_fb_return(fb);
  }
  return res;
}

void handleRoot() {
  String ip = WiFi.localIP().toString();
  String html = "<h1>ESP32-CAM Online</h1>";
  html += "<p><a href='http://" + ip + ":81/stream'>View Stream</a></p>";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\nESP32-CAM Starting...");

  pinMode(4, OUTPUT); // LED pin
  
  // WiFi setup
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  int timeout = 20;
  while (WiFi.status() != WL_CONNECTED && timeout > 0) {
    delay(500);
    Serial.print(".");
    timeout--;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi OK!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi FAILED - check SSID/password");
    return;
  }

  // Camera init
  Serial.println("Initializing camera...");
  if(init_camera() != ESP_OK) {
    Serial.println("Camera init FAILED");
    return;
  }
  Serial.println("Camera OK");

  // HTTP server
  server.on("/", handleRoot);
  server.begin();
  Serial.print("Stream at: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
}

void loop() {
  server.handleClient();
  delay(1);
}
EOF

# Download camera pins:
wget -q https://raw.githubusercontent.com/espressif/esp32-camera/master/camera_pins.h

echo "✅ Sketch created"
ls -la
```

### Edit WiFi Credentials:

```bash
# Open the sketch and EDIT THESE LINES:
# Find: const char* ssid = "YOUR_WIFI_NAME";
# Replace with your actual WiFi network name

# Find: const char* password = "YOUR_WIFI_PASSWORD";
# Replace with your actual WiFi password

# For example:
# const char* ssid = "Natraj_Home_WiFi";
# const char* password = "MySecurePassword123";

nano esp32_camera_stream.ino
# Find the lines above, edit them, save (Ctrl+X, Y, Enter)
```

**ACTION:** Edit the two WiFi lines, save the file

---

## ✅ STEP 4: Compile & Upload (5 minutes)

### Step 4A: Compile

```bash
cd ~/Arduino/esp32_camera_stream

# Compile the sketch:
~/.local/bin/arduino-cli compile \
  --fqbn esp32:esp32:esp32cam \
  --libraries-dir /media/natraj/ARDUINO_USB/arduino_data/libraries \
  .

# Should end with: "Sketch uses X bytes"
# If ERROR: Fix the WiFi SSID/password and try again
```

**ACTION:** Run compile command, verify it succeeds

---

### Step 4B: Prepare ESP32 for Upload (CRITICAL)

**This step is IMPORTANT - don't skip:**

1. **Locate GPIO0 and GND pins on ESP32-CAM**
2. **Use a jumper wire to connect GPIO0 → GND** (hold it in place)
3. **While GPIO0 is connected to GND, press RESET button**
   - Or unplug USB and plug back in
   - The ESP32 will enter "Download Mode"

You should see in serial monitor after reset:
```
waiting for download
```

**If you don't see that, GPIO0→GND may not be connected properly**

**ACTION:** Connect GPIO0 to GND, reset, see "waiting for download"

---

### Step 4C: Upload

```bash
# Upload the code:
~/.local/bin/arduino-cli upload \
  --fqbn esp32:esp32:esp32cam \
  -p /dev/ttyUSB0 \
  --libraries-dir /media/natraj/ARDUINO_USB/arduino_data/libraries \
  .

# Watch for:
# Uploading................................Done uploading.

# If ERROR "Permission denied": 
# sudo usermod -a -G dialout $USER
# (then logout and login again)
```

**ACTION:** Run upload command, watch for "Done uploading"

---

## ✅ STEP 5: Boot & Get IP Address (2 minutes)

### After upload finishes:

1. **DISCONNECT the GPIO0→GND jumper wire**
2. **Press RESET button or plug in USB again**
3. **Open serial monitor:**

```bash
minicom -D /dev/ttyUSB0 -b 115200

# Watch for boot logs:
# ESP32-CAM Starting...
# Connecting to: YOUR_WIFI_NAME
# ....
# WiFi OK!
# IP: 192.168.1.45  ← ⭐ WRITE THIS DOWN

# Stream at: http://192.168.1.45:81/stream
```

**COPY THE IP ADDRESS - You'll need this!**

Exit minicom: `Ctrl+A`, `Q`, `Y`

**ACTION:** Note down the IP address shown

---

## ✅ STEP 6: Test Camera Stream (2 minutes)

### Test in Browser:

Replace `192.168.1.45` with YOUR IP from Step 5:

```bash
# Option A: Firefox/Chrome browser
firefox http://192.168.1.45:81/stream
# You should see LIVE VIDEO STREAM

# Option B: Command line test
curl -v http://192.168.1.45:81/stream | head -c 500
# Should show binary MJPEG data (looks like gibberish - correct!)
```

**If you see video or binary data: 🎉 SUCCESS!**  
**If timeout: Check WiFi, try different WiFi channel, or verify IP**

**ACTION:** Open stream URL or curl it

---

## ✅ STEP 7: Update ROS Launch File (1 minute)

Now that you have the IP, use it in ROS:

```bash
cd ~/file
source install/setup.bash

# Launch with YOUR IP:
ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://192.168.1.45:81/stream
```

**Replace `192.168.1.45` with YOUR actual IP**

**ACTION:** Launch the system with correct IP

---

## 📊 Total Time: ~20 minutes

| Step | Time | Action |
|------|------|--------|
| 1. Hardware | 5 min | Plug in USB, verify lsusb |
| 2. Serial test | 2 min | Boot logs visible? |
| 3. Create sketch | 3 min | Edit WiFi credentials |
| 4. Compile & Upload | 5 min | GPIO0→GND, compile, upload |
| 5. Boot & IP | 2 min | Note IP address |
| 6. Test stream | 2 min | View in browser |
| 7. ROS launch | 1 min | Launch with IP |

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Nothing in serial monitor | Wrong baud (try 74880), check USB cable |
| "Waiting for download" never appears | GPIO0→GND not connected, try holding reset |
| Upload timeout | Keep GPIO0→GND connected during upload |
| WiFi says "FAILED" | Check SSID/password spelling, must be 2.4GHz WiFi |
| Camera stream times out | Check both in same network, check firewall |
| ROS "connection refused" | Take your IP from minicom, not guessing |

---

## 📋 Checklist

- [ ] USB device visible with `lsusb`
- [ ] Serial monitor shows boot logs
- [ ] WiFi credentials edited in sketch
- [ ] Sketch compiles without errors
- [ ] GPIO0→GND connected
- [ ] Upload completes "Done uploading"
- [ ] GPIO0→GND disconnected after upload
- [ ] Serial monitor shows WiFi IP address
- [ ] Browser shows camera stream
- [ ] ROS launch command works

---

**👉 START WITH: STEP 1 - Check USB connection**

**Report back when you get the IP address from the serial monitor!**
