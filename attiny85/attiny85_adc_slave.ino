// Attiny85 Slave code that broadcasts
//ADC reading over I2C when requested

// Address of the slave
#define I2C_SLAVE_ADDRESS 0x4
 
#include <TinyWireS.h>

const uint8_t analogInPin = A3; 
uint16_t      reading     = 0;
boolean       firstByte   = true; 

void setup()
{
    TinyWireS.begin(I2C_SLAVE_ADDRESS); // join i2c network
    TinyWireS.onRequest(requestEvent);
}
 
void loop()
{
    // This needs to be here
    TinyWireS_stop_check();
    reading = analogRead(analogInPin);
}
 
// Gets called when the ATtiny receives an i2c request
// Sending a uint16_t will involve two requests in sequence
void requestEvent()
{
  if (firstByte)
  {
    //byte lbyte = (byte) ((reading >> 8) & 0xff);
    byte lbyte = (byte) (reading >> 8);
    TinyWireS.send(lbyte);
    firstByte = false;
  }
  else
  {
    byte hByte = (byte) (reading & 0xff);
    TinyWireS.send(hByte);
    firstByte = true;
    //reading++;
  }
}
