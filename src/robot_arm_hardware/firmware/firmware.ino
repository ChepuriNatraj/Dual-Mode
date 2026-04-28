#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Initialize PCA9685 at default I2C address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Servo timing parameters (may need physical calibration for your MG996R/SG90 servos)
#define SERVOMIN  150 // This is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  600 // This is the 'maximum' pulse length count (out of 4096)
#define USMIN  600 // This is the rounded 'minimum' microsecond length
#define USMAX  2400 // This is the rounded 'maximum' microsecond length
#define SERVO_FREQ 50 // Analog servos run at ~50 Hz updates

// Buffer for parsing serial commands
const int MAX_JOINTS = 6;
int servo_targets[MAX_JOINTS] = {45, 0, 0, 45, 90, 45}; // Calibrated Home positions in degrees

void setup() {
  Serial.begin(115200);
  delay(150); // Allow USB serial to settle without blocking command loop
  
  // Explicitly set ESP32 default I2C pins (SDA=21, SCL=22)
  Wire.begin(21, 22);

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ); 
  delay(10);
  
  // Set initial default positions
  for(int i = 0; i < MAX_JOINTS; i++) {
    writeServoAngle(i, servo_targets[i]);
  }
  Serial.println("Hardware initialized. Waiting for ROS2 commands...");
}

void loop() {
  // Simple protocol definition: <J0>,<J1>,<J2>,<J3>,<J4>,<J5>\n
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    parseAndExecuteCommand(data);
  }
}

// Function to safely map degrees to PCA9685 microsecond pulses
void writeServoAngle(uint8_t n, double angle) {
  // Constrain to typical servo bounds
  if(angle < 0) angle = 0;
  if(angle > 180) angle = 180;
  
  // Map angle (0 - 180) to pulse width length (USMIN - USMAX) 
  double pulselength = map(angle, 0, 180, USMIN, USMAX);
  pwm.writeMicroseconds(n, pulselength);
}

void parseAndExecuteCommand(String command) {
  int splitIndex = 0;
  int j = 0;
  
  // Parse command separated by commas
  while (j < MAX_JOINTS && command.length() > 0) {
    splitIndex = command.indexOf(',');
    if (splitIndex == -1) {
      servo_targets[j] = command.toInt();
      command = "";
    } else {
      servo_targets[j] = command.substring(0, splitIndex).toInt();
      command = command.substring(splitIndex + 1);
    }
    
    // Apply angle to PCA9685
    writeServoAngle(j, servo_targets[j]);
    j++;
  }
  
  // Echo back for verification (optional)
  Serial.println("OK");
}
