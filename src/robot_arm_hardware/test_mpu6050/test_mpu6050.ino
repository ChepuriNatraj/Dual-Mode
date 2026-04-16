#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

void setup(void) {
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // Wait for serial port to open
  }

  Serial.println("Adafruit MPU6050 Test!");

  // Initialize I2C with pins SDA=21, SCL=22 for ESP32
  Wire.begin(21, 22);

  // Try to initialize!
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip. Please check wiring!");
    Serial.println("SDA -> GPIO 21");
    Serial.println("SCL -> GPIO 22");
    Serial.println("VCC -> 3.3V");
    Serial.println("GND -> GND");
    while (1) {
      delay(10); // Halt execution if sensor not found
    }
  }
  
  Serial.println("MPU6050 Found!");

  // Setup basic sensor ranges
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  Serial.println("Setup complete, starting to read data...\n");
  delay(100);
}

void loop() {
  // Get new sensor events with the readings
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Print Acceleration
  Serial.print("Acceleration X: ");
  Serial.print(a.acceleration.x);
  Serial.print(", Y: ");
  Serial.print(a.acceleration.y);
  Serial.print(", Z: ");
  Serial.print(a.acceleration.z);
  Serial.println(" m/s^2");

  // Print Rotation (Gyroscope)
  Serial.print("Rotation X: ");
  Serial.print(g.gyro.x);
  Serial.print(", Y: ");
  Serial.print(g.gyro.y);
  Serial.print(", Z: ");
  Serial.print(g.gyro.z);
  Serial.println(" rad/s");

  // Print Temperature
  Serial.print("Temperature: ");
  Serial.print(temp.temperature);
  Serial.println(" degC");

  Serial.println("-----------------------------------------");
  
  // Wait half a second before the next reading so it's readable
  delay(500);
}
