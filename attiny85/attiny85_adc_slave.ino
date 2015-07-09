// Attiny85 Slave code that broadcasts
//ADC reading over I2C when requested

// Address of the slave
#define I2C_SLAVE_ADDRESS 0x4

#include <TinyWireS.h>

// The default buffer size, Can't recall the scope of defines right now
#ifndef TWI_RX_BUFFER_SIZE
#define TWI_RX_BUFFER_SIZE ( 1 )
#endif

const uint8_t analogInPin  = A3;
const uint8_t digitalInPin = A2;
uint16_t      readings[2];
boolean       firstByte    = true;
//Variable that will be used in the future when user has register select commands
uint8_t       reg_idx      = 1;

void setup()
{
    TinyWireS.begin(I2C_SLAVE_ADDRESS); // join i2c network
    TinyWireS.onRequest(requestEvent);
}
 
void loop()
{
    // This needs to be here
    TinyWireS_stop_check();

    // Querry the sensors and store it in the buffer
    readings[0] = digitalRead(digitalInPin);
    readings[1] = analogRead(analogInPin);
}

void receiveEvent(uint8_t reg_addr)
{
}

// Gets called when the ATtiny receives an i2c request
// Sending a uint16_t will involve two requests in sequence
void requestEvent()
{
  if (firstByte)
  {
    //byte lbyte = (byte) ((reading >> 8) & 0xff);
    byte lbyte = (byte) (readings[reg_idx] >> 8);

    //multiplex both readings in one number since the ADC is 10 bit.
   //The MSB is the pin state
    if (readings[0]) lbyte |= 0x80;
    TinyWireS.send(lbyte);
    firstByte = false;
  }
  else
  {
    byte hByte = (byte) (readings[reg_idx] & 0xff);
    TinyWireS.send(hByte);
    firstByte = true;
    //reading++;
  }
}
