// Attiny85 Slave code that broadcasts
// analgoue digitals over Uart when requested

// Define Pins for Software Serial

#include <SoftwareSerial.h>

#define rxPin 0
#define txPin 2

const uint8_t analogInPin = A3;
const uint8_t digitalInPin = A2;
uint8_t       ser_byte = 0;
uint16_t      readings[2];

SoftwareSerial tinySerial(rxPin, txPin);

void setup()
{
   pinMode(digitalInPin, INPUT);
   tinySerial.begin(9600);
}
 
void loop()
{
    // Update the readings in memory
    readings[0] = digitalRead(digitalInPin);
    readings[1] = analogRead(analogInPin);

    // If there is a serial byte available
    if (tinySerial.available() > 0) {

      // Read incoming byte:
      ser_byte = tinySerial.read();

      //Safety delay
      delay(2);

      // Only two attiny pins are exposed, only look for ascii 0,1
      if (ser_byte >= 49 && ser_byte <= 50)
      {
        // Convert from ASCII to int
        ser_byte -= 49;
        // Return the requested position in the buffer
        tinySerial.println(readings[ser_byte]);
      }
    }
}
