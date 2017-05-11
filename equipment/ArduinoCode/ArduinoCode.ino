#define BACKLIGHT_PIN 7 // Digital output pin that backlight is attached to
#define TOPLED_PIN 9  // Analog output pin that the TOPLED is attached to
#define BOTTOMLED_PIN 11  // Analog output pin that the BOTTOMLED is attached to
int PHOTODETECTOR_PIN = A0;  // Analog input pin that the Photodetector is attached to
#define LASER_PIN 6 // Digital output pin for Laser ON/OFF

int intensityValue = 0;     // value read from the Photodetector
int outputValue = 0;        // value output to the PWM (analog out)
char intensityLED=0;
char inData[5];             // Allocate 4 characters for the string send over serial port + 1 stop character
char inChar;                  // Where to store the character read
char value[4];
int valueint;
bool newdata_state=0;
byte index = 0; // Index into array; where to store the character
char device = 0;
int F = 400;  // default laser pulse frequency of 400Hz

void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  //pinMode(PHOTODETECTOR_PIN, INPUT);
  pinMode(BOTTOMLED_PIN, OUTPUT);
  pinMode(TOPLED_PIN, OUTPUT);
  pinMode(BACKLIGHT_PIN, OUTPUT);
  pinMode(LASER_PIN, OUTPUT);
  
  digitalWrite(BACKLIGHT_PIN, 0);
  digitalWrite(LASER_PIN, 0);
}

void loop()
{
  // read the analog in value:
  intensityValue = analogRead(PHOTODETECTOR_PIN);
  // map it to the range of the analog out:
  //outputValue = map(intensityValue, 0, 1023, 0, 255);
  // wait 2 milliseconds before the next loop
  // for the analog-to-digital converter to settle
  // after the last reading:
  
  delay(2);
       
  while(Serial.available() > 0) // Don't read unless you know there is data
    {
      inChar = Serial.read(); // Read a character
      inData[index] = inChar; // Store last character into inData at current index
      index++; // Increment where to write next
      if (index==4) // each input/request is 4 characters long, with first character being the device ('S', 'B', 'T', or 'P'), and the remainder being a value (or extra)
      {
      device=inData[0];           //Takes first letter of sent String to decide what Device to talk to
      value[0]=inData[1];         //Takes 2nd to 4th character of sent String as value
      value[1]=inData[2];
      value[2]=inData[3];
      valueint = atoi(value);     //convert string to integer
      
      index=0;  // reset index to 0
      inData[index] = '\0'; // Null terminates the string
      newdata_state=1;
      Serial.flush();
      }
   }
    
  if (newdata_state==1)
    {
    if (device=='S') 
        {
        if (valueint>0)
          {
          digitalWrite(BACKLIGHT_PIN, 1);
          Serial.print("Device is ");
          Serial.print(device);  
          Serial.print(", Value is ");   
          Serial.print(valueint);
          Serial.println(", set backlight on");
          }
        if (valueint==0)
          { 
          digitalWrite(BACKLIGHT_PIN, 0);
          Serial.print("Device is ");
          Serial.print(device);  
          Serial.print(", Value is ");   
          Serial.print(valueint);
          Serial.println(", set backlight off");
          }
        }
    else if (device=='L') 
        {
        if (valueint>0)
          {
          tone(LASER_PIN, F);
          Serial.print("Device is ");
          Serial.print(device);  
          Serial.print(", Value is ");   
          Serial.print(valueint);
          Serial.println(", set laser on");
          }
        if (valueint==0)
          { 
          noTone(LASER_PIN);
          Serial.print("Device is ");
          Serial.print(device);  
          Serial.print(", Value is ");   
          Serial.print(valueint);
          Serial.println(", set laser off");
          }
        }
    else if (device=='F')
      {
        F = valueint; 
        Serial.print("Device is ");
        Serial.print(device);  
        Serial.print(", Value is ");   
        Serial.print(valueint);
        Serial.println(", Set new laser pulse frequency");
      }  
    else if (device=='B') 
      {
        analogWrite(BOTTOMLED_PIN, map(valueint, 0, 100, 0, 255));
        Serial.print("Device is ");
        Serial.print(device);  
        Serial.print(", Value is ");   
        Serial.print(valueint);
        Serial.println(", Set new bottom intensity");
      } 
    else if (device=='T') 
      {
        analogWrite(TOPLED_PIN, map(valueint, 0, 100, 0, 255));
        Serial.print("Device is ");
        Serial.print(device);  
        Serial.print(", Value is ");   
        Serial.print(valueint);
        Serial.println(", Set new top intensity");
      }
    else if (device=='P')  
      {
        //Serial.print("Intensity of the photodetector is: ");
        //Serial.println(500);
        Serial.println(intensityValue);  
      }
      
    newdata_state=0;
    }
}

