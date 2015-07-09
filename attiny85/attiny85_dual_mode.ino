// Attiny85 Slave code that broadcasts
// ADC and PIN state reading over I2C or UART

// Address of the slave
#define I2C_SLAVE_ADDRESS 0x4
 
#include <TinyWireS.h>
#include <SoftwareSerial.h>

// The default buffer size, Can't recall the scope of defines right now
#ifndef TWI_RX_BUFFER_SIZE
#define TWI_RX_BUFFER_SIZE ( 8 )
#endif

// Define Pins for Software Serial
#define RXPIN 0
#define TXPIN 2

#define IFACE_THRSHOLD (5000)

const uint8_t analogInPin  = A3;
const uint8_t digitalInPin = A2;
boolean       firstByte    = true;
boolean       hw_detect    = true;
uint8_t       ser_byte     = 0;

// will store startup-time
unsigned long startMillis  = 0;

// Operation mode 0= Serial, 1 = I2C
uint8_t       mode         = 0;

// Variable that will be used in the future when user has register select commands
uint8_t       reg_idx      = 1;

// Readings buffer
uint16_t      readings[2];
SoftwareSerial tinySerial(RXPIN, TXPIN);

void setup()
{
    serial_setup();
    startMillis = millis();
}

/* Enable i2c */
void i2c_setup()
{
    TinyWireS.begin(I2C_SLAVE_ADDRESS); // join i2c network
    TinyWireS.onRequest(requestEvent);
}

/* Enable Serial */
void serial_setup()
{
   pinMode(digitalInPin, INPUT);
   tinySerial.begin(9600);
}

/* Disable serial mode */
void serial_end()
{
    tinySerial.end();
}

/* Main loop for UART mode */
void serial_loop()
{
    // This needs to be here
    readings[0] = digitalRead(digitalInPin);
    readings[1] = analogRead(analogInPin);

    if (tinySerial.available() > 0) {
      // get incoming byte:
      ser_byte = tinySerial.read();

      //Safety delay
      delay(2);
      if (ser_byte >= 49 && ser_byte <= 50)
      {
        //Convert from ASCII to int
        ser_byte -= 49;
        //Return the requested position in the buffer
        tinySerial.println(readings[ser_byte]);
      }
    }
}

/* Main loop for i2c mode */
void i2c_loop()
{
    // This needs to be here
    TinyWireS_stop_check();
    
    // Querry the sensors and store it in the buffer
    readings[0] = digitalRead(digitalInPin);
    readings[1] = analogRead(analogInPin);
}

/* Main loop, hwdetect, and select from the two operation loops */
void loop()
{
    // If in hardware detect mode
    if (hw_detect)
    {
      detect_jumper();
    }
    // Main operation mode
    else
    {
      if (mode) i2c_loop();
      else serial_loop();
    }   
}


/* Attempt todetect operation mode */
void detect_jumper()
{
  unsigned long currentMillis = millis();

  // Wait for a byte from Serial to remain in Serial mode
  if (tinySerial.available() > 0) {
    hw_detect = false;
    tinySerial.println("OK");
  }
  // If timeout is reached it resets to I2C mode
  else if (currentMillis - startMillis >= IFACE_THRSHOLD)
  {
    serial_end();
    i2c_setup();
    mode = 1;
    hw_detect = false;
  }
}

/* Placeholder for write operations coming from master */
void receiveEvent(uint8_t reg_addr)
{
}

/* Gets called when the ATtiny receives an i2c request
   Sending a uint16_t will involve two requests in sequence */
void requestEvent()
{
  if (firstByte)
  {
    //byte lbyte = (byte) ((reading >> 8) & 0xff);
    byte lbyte = (byte) (readings[reg_idx] >> 8);
    // multiplex both readings in one number since
    // the ADC is 10 bit.The MSB is the pin state
    if (readings[0]) lbyte |= 0x80;
    TinyWireS.send(lbyte);
    firstByte = false;
  }
  else
  {
    byte hByte = (byte) (readings[reg_idx] & 0xff);
    TinyWireS.send(hByte);
    firstByte = true;
  }
}
