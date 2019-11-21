//Control program for the SRT drives

//set up the pins

#define FF2Az  4     //purple
#define FF1Az  5     //blue
#define FF2Alt  6    //purple
#define FF1Alt  7    //blue

#define RESETAz  22  //black
#define RESETAlt 24  //white

#define PWMAz 8      //green
#define PWMAlt 10    //green

#define DIRAz 9      //yellow
#define DIRAlt 11    //yellow

#define impulseAz 12      //blue check these are the right way around!
#define impulseAlt 13    //orange



void setup() {
// setup the input pins. Note that FF signals are inverted wrt the motor driver board
  pinMode(FF1Az,INPUT);  
  pinMode(FF2Az,INPUT);
  pinMode(FF1Alt,INPUT);  
  pinMode(FF2Alt,INPUT);
  pinMode(impulseAlt,INPUT);  
  pinMode(impulseAlt,INPUT);
// setup the output pins and initialise to sensible values.
  pinMode(RESETAz,OUTPUT);   digitalWrite(RESETAz,HIGH);
  pinMode(RESETAlt,OUTPUT);  digitalWrite(RESETAlt,HIGH);
  pinMode(PWMAz,OUTPUT);     digitalWrite(PWMAz,LOW);
  pinMode(PWMAlt,OUTPUT);    digitalWrite(PWMAlt,LOW);
  pinMode(DIRAz,OUTPUT);     digitalWrite(DIRAz,LOW);
  pinMode(DIRAlt,OUTPUT);    digitalWrite(DIRAz,LOW);
// setup the serial port for writing out  
  Serial.begin(9600);
}

void loop() {
  int i;
   analogReadResolution(12); // maximum resolution of the ADC

//ramp up and dowm in speed, reading out the current for some of it

  digitalWrite(DIRAz,LOW);
//ramp up
  for (int i=0; i <= 254; i++){
      analogWrite(PWMAz,255-i);
       float current = (5.0/4096.0*analogRead(A1) -2.5)/.066;
       Serial.print(current);Serial.println(" amps");
      delay(10);
   } 
   delay(1000);
//ramp down   
   for (int i=0; i <= 255; i++){
      analogWrite(PWMAz,i);
      delay(10);
   } 
 delay(1000);
//now the other way
  digitalWrite(DIRAz,HIGH);
//ramp up
  for (int i=0; i <= 254; i++){
      analogWrite(PWMAz,255-i);
      delay(10);
   } 
   delay(1000);
///ramp down   
   for (int i=0; i <= 255; i++){
      analogWrite(PWMAz,i);
      delay(10);
   }
 delay(1000);  
}
