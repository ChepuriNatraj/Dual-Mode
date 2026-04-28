#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define USMIN 600
#define USMAX 2400
#define SERVO_FREQ 50

static const uint8_t SERVO_CHANNEL = 0;
static const int START_ANGLE = 40;

int currentAngle = START_ANGLE;

void writeServoAngle(uint8_t channel, int angle) {
  if (angle < 0) angle = 0;
  if (angle > 180) angle = 180;

  uint16_t pulseUs = map(angle, 0, 180, USMIN, USMAX);
  pwm.writeMicroseconds(channel, pulseUs);
}

void printHelp() {
  Serial.println("\nCommands:");
  Serial.println("  <number>   -> set exact angle (0..180)");
  Serial.println("  +          -> +1 degree");
  Serial.println("  -          -> -1 degree");
  Serial.println("  ++         -> +5 degrees");
  Serial.println("  --         -> -5 degrees");
  Serial.println("  p          -> print current angle");
  Serial.println("  h          -> help");
}

void applyAndReport() {
  writeServoAngle(SERVO_CHANNEL, currentAngle);
  Serial.print("Applied angle: ");
  Serial.println(currentAngle);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ);
  delay(10);

  Serial.println("Gripper Limit Finder Ready");
  currentAngle = START_ANGLE;
  applyAndReport();
  printHelp();
}

void loop() {
  if (!Serial.available()) {
    delay(20);
    return;
  }

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd.length() == 0) return;

  if (cmd == "h") {
    printHelp();
    return;
  }

  if (cmd == "p") {
    Serial.print("Current angle: ");
    Serial.println(currentAngle);
    return;
  }

  if (cmd == "+") {
    currentAngle += 1;
    if (currentAngle > 180) currentAngle = 180;
    applyAndReport();
    return;
  }

  if (cmd == "-") {
    currentAngle -= 1;
    if (currentAngle < 0) currentAngle = 0;
    applyAndReport();
    return;
  }

  if (cmd == "++") {
    currentAngle += 5;
    if (currentAngle > 180) currentAngle = 180;
    applyAndReport();
    return;
  }

  if (cmd == "--") {
    currentAngle -= 5;
    if (currentAngle < 0) currentAngle = 0;
    applyAndReport();
    return;
  }

  int requested = cmd.toInt();
  if (requested == 0 && cmd != "0") {
    Serial.print("Unknown command: ");
    Serial.println(cmd);
    printHelp();
    return;
  }

  currentAngle = requested;
  if (currentAngle < 0) currentAngle = 0;
  if (currentAngle > 180) currentAngle = 180;
  applyAndReport();
}
