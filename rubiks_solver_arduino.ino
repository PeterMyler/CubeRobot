#include <Arduino.h>

//#include <Streaming.h>
//#include <Vector.h>

// pulse = High -> Low
// 1 pulse = 1.8 degrees

// define pins numbers
//const int enablePin = 13;  // motor drivers enable pin

//                 motors:     0   1   2   3   4   5
const int motorStepPins[6] = { 2,  4,  6,  8, 10, 12 };
const int motorDirPins[6] =  { 3,  5,  7,  9, 11, 13 };
const int motorNames[6] =   { 'D','F','B','R','L','U' };

int stepDelay = 500;  // delay (us) between each step instruction (330-500+)
int turnDelay = 100;   // delay (ms) bewteen each turn of a motor (0-100+)
int moves = 0;
int extra_moves = 0;

const long BAUD = 115200;


int findName(char ch) {
  for (int i = 0; i < 6; i++) {
    if (ch == motorNames[i]) {
      return i;
    }
  }
  
  return -1;  // couldnt find
}

void executeMove(String move) {
  int motorNum = findName(toupper(move[0]));
  if (motorNum == -1){
    Serial.println("Error! Could not find motor with that name.");
    return;
  }

  int stepP = motorStepPins[motorNum];
  int dirP = motorDirPins[motorNum];

  int steps = 100;
  int dir = 0;

  moves++;

  // set appropriate parameters
  if (move.length() == 2){
    if (move[1] == '2'){
      steps *= 2;
      extra_moves++;
    }
    else {
      dir = 1;
    }
  }

  // execute motor turn
  digitalWrite(dirP, dir);  // dir: 0 = CCW, 1 = CW
  for (int x = 0; x < steps; x++) {
    digitalWrite(stepP, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(stepP, LOW);
    delayMicroseconds(stepDelay);
  }

}


void setup() {
  pinMode(A0, OUTPUT);
  digitalWrite(A0, LOW);
  pinMode(A1, OUTPUT);
  digitalWrite(A1, LOW);

  // setup pins
  for (int i : motorStepPins)
    pinMode(i, OUTPUT);

  for (int i : motorDirPins)
    pinMode(i, OUTPUT);


  Serial.begin(BAUD);
  Serial.setTimeout(5);
  while (!Serial) {
    // wait for serial port to connect.
  }
  delay(500);

  // enable the stepper motors
  digitalWrite(A0, HIGH);
  delay(1000);
  digitalWrite(A1, HIGH);

  Serial.println("Ready");
}

String command = "";
String buffer = "";
unsigned long timer = 0;
float timeTaken = 0;
//Vector<String> commands;

void loop() {
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    if (command[command.length()-1] != ' ') command += ' ';

    // check if first char is a viable move
    if (findName(command[0]) != -1) {
      timer = millis();
      moves = 0;
      extra_moves = 0;

      buffer = "";
      for (char c : command) {
        if (c != ' '){
          buffer += c;
        }
        else {
          executeMove(buffer);
          buffer = "";
          delay(turnDelay);  // 100, 50, 25
        }
      }

      timeTaken = ((float)(millis() - timer - turnDelay)) / 1000;
      Serial.print("Time taken: ");
      Serial.print(timeTaken, 3);
      Serial.print(" seconds. Moves: ");
      Serial.print(moves);
      Serial.print(" (");
      Serial.print(moves + extra_moves);
      Serial.print("). TPS: ");
      Serial.println((moves + extra_moves)/timeTaken, 2);

    } else {
      // change motor settings
      // format: "<stepDelay> <turnDelay>"

      int counter = 0;
      buffer = "";
      for (char c : command) {
        if (c != ' ') {
          buffer += c;
        }
        else {
          if (counter == 0) {
            stepDelay = buffer.toInt();
            buffer = "";
            counter++;
            Serial.print("stepDelay = ");
            Serial.print(stepDelay);
          } else {
            turnDelay = buffer.toInt();
            Serial.print("; turnDelay = ");
            Serial.print(turnDelay);
          }
        }
      }
      Serial.println();

    }

  }
}