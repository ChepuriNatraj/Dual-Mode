#include <ESP32Servo.h>

Servo testServo;

// Recommended PWM GPIO pin on the ESP32
int servoPin = 18; 

void setup() {
  Serial.begin(115200);
  
  // Allow allocation of all timers
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
  testServo.setPeriodHertz(50);      // Standard 50Hz servo
  testServo.attach(servoPin, 500, 2400); // Attach to pin 18 with 500us to 2400us pulses (standard for MG996R)
  
  Serial.println("ESP32 Direct Servo Test Started");
}

void loop() {
  Serial.println("Position: 0 degrees");
  testServo.write(0);
  delay(2000);
  
  Serial.println("Position: 90 degrees");
  testServo.write(90);
  delay(2000);
  
  Serial.println("Position: 180 degrees");
  testServo.write(180);
  delay(2000);
}
