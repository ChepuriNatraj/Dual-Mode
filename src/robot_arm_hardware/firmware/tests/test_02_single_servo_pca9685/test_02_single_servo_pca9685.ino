#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Initialize PCA9685 at default I2C address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Servo timing parameters tailored for MG996R
#define USMIN  600  // Minimum microsecond length (~0 degrees)
#define USMAX  2400 // Maximum microsecond length (~180 degrees)
#define SERVO_FREQ 50 // Standard 50Hz

// We will test the servo attached to port 0 on the PCA9685
uint8_t servoChannel = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("Level 2: ESP32 + PCA9685 Single Servo Test");

  // Explicitly assign I2C pins for ESP32 (SDA = 21, SCL = 22)
  Wire.begin(21, 22);

  pwm.begin();
  pwm.setOscillatorFrequency(27000000); // Standard internal oscillator
  pwm.setPWMFreq(SERVO_FREQ); 
  delay(10);
}

void writeServoAngle(uint8_t channel, double angle) {
  // Constrain bounds
  if(angle < 0) angle = 0;
  if(angle > 180) angle = 180;
  
  // Map angle (0 - 180) to pulse width (USMIN - USMAX) 
  double pulselength = map(angle, 0, 180, USMIN, USMAX);
  pwm.writeMicroseconds(channel, pulselength);
}

void loop() {
  Serial.println("Position: 0 degrees");
  writeServoAngle(servoChannel, 0);
  delay(2000);
  
  Serial.println("Position: 90 degrees");
  writeServoAngle(servoChannel, 90);
  delay(2000);
  
  Serial.println("Position: 40 degrees (safe test)");
  writeServoAngle(servoChannel, 40);
  delay(2000);
}
