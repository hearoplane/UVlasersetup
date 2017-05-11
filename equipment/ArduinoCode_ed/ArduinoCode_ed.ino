#define SHUTTER 8
#define LED_PIN 13



const int analogInPin = A0; // Analog input pin that the Photodetector is attached to
int intensityValue = 0;     // value read from the Photodetector
int outputValue = 0;        // value output to the PWM (analog out)
/*char inData[5];             // Allocate 4 characters for the string send over serial port + 1 stop character
char inChar;                  // Where to store the character read
char value[4];
int valueint;
bool newdata_state=0;
String content = "";
char character;
*/

const int INPUTBUFFER_LENGTH = 150;
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
long inputNumber;
char inputNumberBuffer[INPUTBUFFER_LENGTH];

char cmd_char;



byte index = 0; // Index into array; where to store the character
char device = 0;
const int topAnalogOutPin = 9; // Analog output pin that the TOPLED is attached to
const int bottomAnalogOutPin = 10; // Analog output pin that the BOTTOMLED is attached to

char intensityLED=0;
int shutter_state = 0;
int bottomled_state = 0;

void setup()
{
  // start serial port at 9600 bps:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  pinMode(LED_PIN, OUTPUT);
  pinMode(6, INPUT);  
  pinMode(7, INPUT);  
  digitalWrite(LED_PIN, bottomled_state);
  digitalWrite(SHUTTER, shutter_state);
}

void loop()
{
  // read the analog in value:
  intensityValue = analogRead(analogInPin);
  // map it to the range of the analog out:
  //outputValue = map(intensityValue, 0, 1023, 0, 255);
  // wait 2 milliseconds before the next loop
  // for the analog-to-digital converter to settle
  // after the last reading:
  
  delay(2);


  // check serial port for new data
  serialEvent();


  // handle completed commands
  if (stringComplete) {
    cmd_char = tolower(inputString[0]);
    
    switch(cmd_char){
      case 's':
        inputNumber = interpret_int_from_string(inputString.substring(1));
        if (inputNumber > 0){
          digitalWrite(SHUTTER, 1);
          digitalWrite(LED_PIN, 1);
          Serial.println("Shutter open");
        }
        else {
          digitalWrite(SHUTTER, 0);
          digitalWrite(LED_PIN, 0);
          Serial.println("Shutter closed");
        }
        break;
      case 'b':
        inputNumber = interpret_int_from_string(inputString.substring(1));      
        analogWrite(bottomAnalogOutPin, inputNumber);
        Serial.print("Set new bottom intensity ");
        Serial.println(inputNumber);
        break;    
      case 't':
        inputNumber = interpret_int_from_string(inputString.substring(1));            
        analogWrite(topAnalogOutPin, inputNumber);
        Serial.print("Set new top intensity ");
        Serial.println(inputNumber);
        break;    
      case 'p':
        //Serial.print("Intensity of the photodetector is: ");
        Serial.println(intensityValue);        
        break;
      default:
        Serial.print("unknown cmd: (");
        Serial.print(inputString);
        Serial.println(")");  
    }
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}




////////////

long interpret_int_from_string(String in) {
    in.trim();
    /*for (int i=2; i<INPUTBUFFER_LENGTH; i++){
      inputNumberBuffer[i-2]=in[i];
    }
    */
    in.toCharArray(inputNumberBuffer, INPUTBUFFER_LENGTH);

    return atol(inputNumberBuffer);  
}

int sign(int x) {
    return (x > 0) - (x < 0);
}


// serial interrupt handler
void serialEvent() {
    while (Serial.available()) {
      // get the new byte:
      char inChar = (char)Serial.read(); 
      // add it to the inputString:
      inputString += inChar;
      // if the incoming character is a newline, set a flag
      // so the main loop can do something about it:
      if (inChar == '\n') {
          stringComplete = true;
          //Serial.println(inputString);
  
      }
    }  
}

