# Finding & Configuring Your ESP32-CAM IP Address

> **This is blocking your autonomous sorting launch. Complete this first.**

## 🎯 Quick Status Check

Your current issue:
```
esp32_camera_bridge is trying to connect to: http://192.168.1.100:81/stream
                                             (This is a PLACEHOLDER - doesn't exist)
```

**You need to:** Find your actual ESP32-CAM IP address on your network.

---

## 🔍 Method 1: Router DHCP Table (BEST)

**Fastest way - check your WiFi router:**

1. Open your router admin page (usually `192.168.1.1` or `192.168.0.1`)
2. Login with admin credentials
3. Go to **DHCP > Connected Devices** or **Status > Wireless Devices**
4. Look for a device named:
   - `esp32`
   - `esp32cam`
   - `ESP32-C3` (if using C3 variant)
   - Something with firmware date "Apr 2026"

5. **Note down its IP address** (e.g., `192.168.1.45` or `192.168.0.78`)

---

## 🔍 Method 2: Network Scanning (if Router Method Fails)

If you can't access your router, use network scanning:

```bash
# Install if not already present:
sudo apt-get update && sudo apt-get install -y net-tools arp-scan nmap

# Scan for all devices on your network:
sudo arp-scan -l

# Look for Espressif (ESP32 manufacturer):
# Example output:
#   192.168.1.45        aa:bb:cc:dd:ee:ff       Espressif
```

**Your ESP32-CAM's IP is likely `192.168.1.X` where X is 40-50**

---

## 🔍 Method 3: Serial Monitor (If Both Fail)

Connect ESP32 via USB and check boot logs:

```bash
# Install minicom if needed:
sudo apt-get install -y minicom

# Connect at 115200 baud:
minicom -D /dev/ttyUSB0 -b 115200

# Watch for boot logs, you'll see:
# [WiFi] Connecting to SSID...
# [WiFi] IP Address: 192.168.1.XX  ← THIS IS THE ADDRESS
```

Press `Ctrl+A` then `Q` to exit minicom.

---

## 📌 Once You Have the IP Address

### Step 1: Test Camera MJPEG Stream (Verify It's Working)

```bash
# Open in your browser:
http://YOUR_ACTUAL_IP:81/stream

# Or test with curl:
curl -v http://YOUR_ACTUAL_IP:81/stream | head -c 1000
```

You should see **MJPEG binary video data** (looks like gibberish, which is correct).

### Step 2: Update Launch File with Correct IP

Edit the launch command and replace the placeholder:

```bash
cd ~/file && source install/setup.bash

ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://YOUR_ACTUAL_IP:81/stream
```

**Example with actual IP:**
```bash
ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://192.168.1.45:81/stream
```

### Step 3: Verify Camera Bridge Connects

Watch the logs for:
✅ Good:
```
[INFO] ESP32 Camera Bridge initialized. Connecting to: http://192.168.1.45:81/stream
[INFO] Attempting to connect to http://192.168.1.45:81/stream...
[INFO] Successfully connected to camera stream
```

❌ Bad (still timeout):
```
[ERROR] Failed to open camera stream. Retrying in 2.0s...
```

If you get timeout errors, the IP is still wrong. Go back to Method 1-3.

---

## 🛠️ Troubleshooting Camera Connection

| Problem | Solution |
|---------|----------|
| Can't access router page | Default is usually `http://192.168.1.1` or `192.168.0.1` |
| arp-scan shows no Espressif | ESP32 may not be connected to network - check WiFi LED |
| Camera stream returns 404 | Wrong port - should be `:81` not `:80` |
| Stream works in browser but ROS fails | Firewall may block ROS - try temporarily disabling |
| Still getting timeout after correct IP | Check if both devices on same network (no VPN) |

---

## 🎬 Next Action (Once IP Confirmed)

When your ESP32-CAM IP is confirmed working:

```bash
# Launch full autonomous sorting system:
source ~/file/install/setup.bash

ros2 launch robot_arm_vision hardware_sorting.launch.py \
    serial_port:=/dev/ttyUSB0 \
    baud_rate:=115200 \
    esp32_camera_url:=http://YOUR_IP:81/stream

# In another terminal, verify system:
ros2 node list      # Should show 9 nodes
ros2 topic list     # Should show camera, arm, vision topics
```

---

## 📋 Document Your Settings

Once ESP32-CAM IP is found, write it down:

```
My ESP32-CAM IP Address: ___________________
WiFi SSID it's connected to: ___________________
Router Admin IP: ___________________
```

Keep these for future reference and firmware updates.

---

**⏱️ This should take 2-5 minutes. Let me know your IP address when you have it!**
