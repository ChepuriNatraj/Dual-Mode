#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Initialize PCA9685 at default I2C address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define USMIN  600 
#define USMAX  2400
#define SERVO_FREQ 50
#define NUM_SERVOS 6

void setup() {
  Serial.begin(115200);
  Serial.println("Level 3: Full 6-Servo Stress Test");

  // Explicitly assign I2C pins for ESP32
  Wire.begin(21, 22);

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ); 
  delay(10);
}

void writeServoAngle(uint8_t channel, double angle) {
  if(angle < 0) angle = 0;
  if(angle > 180) angle = 180;
  
  double pulselength = map(angle, 0, 180, USMIN, USMAX);
  pwm.writeMicroseconds(channel, pulselength);
}

// Function to move all 6 servos to the same angle simultaneously
void moveAllServos(double angle) {
  for(uint8_t i = 0; i < NUM_SERVOS; i++) {
    writeServoAngle(i, angle);
  }
}

void loop() {
  Serial.println("Moving all servos to 90 degrees (Home)");
  moveAllServos(90);
  delay(2000);
  
  Serial.println("Moving all servos to 45 degrees");
  moveAllServos(45);
  delay(2000);
  
  Serial.println("Moving all servos to 135 degrees");
  moveAllServos(135);
  delay(2000);
}
