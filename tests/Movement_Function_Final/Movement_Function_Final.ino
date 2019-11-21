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

//these variables are needed for the interrupt code
volatile int countAz = 0;
volatile int countAlt = 0;
volatile unsigned long lastpulseAz = 0;
volatile unsigned long lastpulseAlt = 0;

//these variables are used in the gotoAltAz() function
float Alt = 0;
float Az = 0;
int ALT = 0;
int AZ = 0;

//these variables are used in the reldrive() function
float X = 0;
float Y = 0;

//these variables are used both in the gotoAltAz() and reldrive() functions
int alt = 0;
int az = 0;

//these constants are used in the SetHome() function and are the coordinates for the home position in the SRT as given in the srt.cat file
float HomeAlt = -1;
float HomeAz = 179;

//these constants are used in the SafetyCheck() function
int val1 = 0;
int val2 = 0;
int val3 = 0;
int val4 = 0;

void setup() {
//setup the input pins. 
  pinMode(FF1Az,INPUT);  
  pinMode(FF2Az,INPUT);
  pinMode(FF1Alt,INPUT);  
  pinMode(FF2Alt,INPUT);
  pinMode(impulseAz,INPUT);  
  pinMode(impulseAlt,INPUT);
//setup the output pins and initialise to sensible values. 
  pinMode(RESETAz,OUTPUT);   digitalWrite(RESETAz,HIGH);
  pinMode(RESETAlt,OUTPUT);  digitalWrite(RESETAlt,HIGH);
//Note that the  DIR and PWM pins are inverted before they reach the controller board
  pinMode(PWMAz,OUTPUT);     digitalWrite(PWMAz,HIGH);
  pinMode(PWMAlt,OUTPUT);    digitalWrite(PWMAlt,HIGH);
  pinMode(DIRAz,OUTPUT);     digitalWrite(DIRAz,HIGH);
  pinMode(DIRAlt,OUTPUT);    digitalWrite(DIRAlt,HIGH);
attachInterrupt(impulseAz, reedAz, FALLING);
attachInterrupt(impulseAlt, reedAlt, FALLING);
//setup the serial port for writing in and out 
  Serial.begin(9600);
}

void loop() {
SafetyCheck();
if (Serial.available() > 0) {
  int Function = Serial.parseInt();
  switch (Function) {
    case 1:
    SetHome();
    break;
    case 2:
    //look for the next valid float in the incoming serial stream:
    float a = Serial.parseFloat();
    //do it again:
    float b = Serial.parseFloat();
      //print :
      Serial.print(a, DEC); Serial.print(" "); Serial.println(b, DEC);
      gotoAltAz(a,b);
      break;
    case 3:
    //look for the next valid float in the incoming serial stream:
    float x = Serial.parseFloat();
    //do it again:
    float y = Serial.parseFloat();
      //print :
      Serial.print(x, DEC); Serial.print(" "); Serial.println(y, DEC);
      reldrive(x,y);
      break;
  }
}
}

//The reed functions are to do with the interrupt and impulse counts
void reedAlt() {
  unsigned long currentMillisAlt = millis();
 if ((unsigned long)(currentMillisAlt - lastpulseAlt) >= 15) //only increment if more than 15ms since last pulse
   {
     countAlt = countAlt + 1;
   }
  lastpulseAlt = millis();
}

void reedAz() {
  unsigned long currentMillisAz = millis();
 if ((unsigned long)(currentMillisAz - lastpulseAz) >= 15) //only increment if more than 15ms since last pulse
   {
     countAz = countAz + 1;
   }
  lastpulseAz = millis();
}

//this function does a safety check on the SRT drives, this is performed each time the SRT and arduino are switched on and a program is ran
void SafetyCheck() {
  val1=digitalRead(FF1Az);
  val2=digitalRead(FF2Az);
  val3=digitalRead(FF1Alt);
  val4=digitalRead(FF2Alt);
  if (val2==HIGH) {
    digitalWrite(PWMAz, HIGH);
    digitalWrite(PWMAlt, HIGH);
    Serial.println("Azimtuh drive short circuit! Seek assistance!");
  }
  if (val4==HIGH) {
    digitalWrite(PWMAz, HIGH);
    digitalWrite(PWMAlt, HIGH);
    Serial.println("Altitude drive short circuit! Seek assistance!");
  }
  if (val1==HIGH) {
    digitalWrite(PWMAz, HIGH);
    digitalWrite(PWMAlt, HIGH);
    Serial.println("Azimuth drive over temperature! Seek assistance!");
  }
  if (val3==HIGH) {
    digitalWrite(PWMAz, HIGH);
    digitalWrite(PWMAlt, HIGH);
    Serial.println("Altitude drive over temperature! Seek assistance!");
  }
  if (val1==HIGH && val2==HIGH) {
    digitalWrite(PWMAz, HIGH);
    digitalWrite(PWMAlt, HIGH);
    Serial.println("Azimuth drive under voltage! Seek assistance!");
  }
  if (val3==HIGH && val4==HIGH) {
    digitalWrite(PWMAz, HIGH);
    digitalWrite(PWMAlt, HIGH);
    Serial.println("Altitude drive under voltage! Seek assistance!");
  }
}
  
//this function takes the telescope to the home position
void SetHome() {
     analogReadResolution(12); // maximum resolution of the ADC
     digitalWrite(DIRAz,LOW);  // drive to west
     digitalWrite(PWMAz,LOW);  // start the Az motor at max speed
     digitalWrite(DIRAlt,LOW);// drive to horizon
     digitalWrite(PWMAlt,LOW); // start the Alt motor at max speed
     Serial.println("Driving to the home position...");
     delay (500);
//wait until we reach the limit switches
      do {} 
      while ((millis() - lastpulseAlt) < 2000 || (millis() - lastpulseAz) < 2000); 
/*now moves the SRT to the home position coordinates as stated in the srt.cat file (rough estimate of coordinates, will need to be checked) by moving
  the SRT drives a fixed amount of pulses based on it's position after it moves to the furthest points possible in the 'LOW' directions of both drives*/
     countAlt=0;
     countAz=0;
     digitalWrite(DIRAz,HIGH);  // drive to east
     digitalWrite(PWMAz,LOW);  // start the Az motor at max speed
     digitalWrite(DIRAlt,HIGH);// drive to horizon
     digitalWrite(PWMAlt,LOW); // start the Alt motor at max speed
     do {
       if (6 > countAlt) {
         analogWrite(PWMAlt,(218-(pow((6-countAlt),2))));
       }
       else { analogWrite(PWMAlt,255);
       }

       if (82 > countAz) {
         analogWrite(PWMAz,(218-(pow((82-countAz),2))));
       }
       else { analogWrite(PWMAz,255);
       }
     }
     while (3 > countAlt || 82 > countAz);
//reset the counters at this position
    analogWrite(PWMAz, 255);
    analogWrite(PWMAlt, 255);
    Serial.print("At the home position."); Serial.print(" Home Altitude: "); Serial.print(HomeAlt); Serial.print(" Home Azimuth: "); Serial.println(HomeAz);
    countAlt=0;
    countAz=0;
//The home position coordinates from the srt.cat file have only been estimated here and the SRT may not be exactly at these, should be checked   
}

/*moves the telescope from the home position to specific altitude and azimuth coordinates (only for one 'side' of the SRT, have not worked on when it
  needs to be flipped on its head */
void gotoAltAz(float Alt,float Az) {
  countAlt=0;
  countAz=0;
/*the Alt and Az inputs need to be doubled as there are two pulses in every degree, and one pulse in half a degree of movement, this is why the majority
  of the number in the rest of this function seem large as they have all been doubled to remain consistent so that the code works*/
  alt=(Alt*2);
  az=(Az*2);
  analogReadResolution(12); // mazimum resolution of the ADC
  do {
    if (alt < -4 || alt > 90) {
      Serial.println("This is beyond the range of the SRT's altitude drive.");
    }
    if (az > 440 && az < 560) {
      Serial.println("This is beyond the range of the SRT's azimuth drive. Flip the SRT's direction with the altitude drive to reach these coordinates.");
    }
    if (az < 0 || az > 360) {
      Serial.println("This azimuth coordinate is not possible.");
    }
//from -1 degrees (home altitude coordinate) to the limit of -2 degrees in altitude, limit due to the range of the drive, not exact, should be checked
    if (alt < -2 && alt >= -4) {
      ALT = ((-alt) - 2);
      if (ALT > countAlt) {
        digitalWrite(DIRAlt,LOW);
        analogWrite(PWMAlt,(218-(pow((ALT-countAlt),2))));
      }
      else { analogWrite(PWMAlt,255);
      }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
//from -1 degrees (home altitude coordinate) to 0 degrees in altitude
    if (alt > -2 && alt <= 0) {
      ALT = (2 - (-alt));
      if (ALT > countAlt) {
        digitalWrite(DIRAlt,HIGH);
        analogWrite(PWMAlt,(218-(pow((ALT-countAlt),2))));
      }
      else { analogWrite(PWMAlt,255);
      }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
//from 0 degrees to 90 degrees in altitude
    if (alt > 0 && alt <= 90) {
      ALT = (2 + alt);
      if (ALT > countAlt) {
        digitalWrite(DIRAlt,HIGH);
        analogWrite(PWMAlt,(218-(pow((ALT-countAlt),2))));
      }
      else { analogWrite(PWMAlt,255);
      }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
//from 179 degrees (home azimuth coordinate) to the limit of 220 degrees in azimuth, limit due to the range of the drive, not exact, should be checked
    if (az <= 440 && az > 358) {
      AZ = (az - 358);
      if (AZ > countAz) {
        digitalWrite(DIRAz,LOW);
        analogWrite(PWMAz,(218-(pow((AZ-countAz),2))));
      }
      else { analogWrite(PWMAz,255);
      }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
//from 179 degrees (home azimuth coordinate) to 0 degrees in azimuth (north), not exact, should be checked
    if (az < 358 && az >= 0) {
      AZ=(358 - az);
      if (AZ > countAz) {
        digitalWrite(DIRAz,HIGH);
        analogWrite(PWMAz,(218-(pow((AZ-countAz),2))));
      }
      else { analogWrite(PWMAz,255);
      }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
//from 0 degrees (north) to the limit of 280 degrees in azimuth, limit due to the range of the drive, not exact, should be checked
    if (az < 720 && az >= 560) {
      AZ = (358 + (720 - alt));
      if (AZ > countAz) {
        digitalWrite(DIRAz,HIGH);
        analogWrite(PWMAz,(218-(pow((AZ-countAz),2))));
      }
      else { analogWrite(PWMAz,255);
      }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
  }
   while ((sqrt(alt*alt)) > countAlt || (sqrt(az*az)) > countAz);
   analogWrite(PWMAz, 255);
   analogWrite(PWMAlt, 255);
   Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
} 
  
/*drives the telescope from a position to any other position in specified degree or half degree increments, the speed of the drive changes according to the distance
  between current location and target location*/
void reldrive(float X,float Y) {
  countAlt=0;
  countAz=0;
  alt=(X*2);
  az=(Y*2);
  analogReadResolution(12); // maximum resolution of the ADC
  do {
  // altitude drive
  if (alt > 0) {
    digitalWrite(DIRAlt,HIGH);
    if (alt > countAlt) {
      analogWrite(PWMAlt,(218-(pow((alt-countAlt),2))));
    }
    else { analogWrite(PWMAlt,255);
    }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
  if (alt < 0) {
    digitalWrite(DIRAlt,LOW);
    if (-alt > countAlt) {
      analogWrite(PWMAlt,(218-(pow(((-alt)-countAlt),2))));
    }
    else { analogWrite(PWMAlt,255);
    }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
    }
    //azimtuth drive
  if (az > 0) {
    digitalWrite(DIRAz,HIGH);
    if (az > countAz) {
       analogWrite(PWMAz,(218-(pow((az-countAz),2))));
     }
     else { analogWrite(PWMAz,255);
    }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
     }
  if (az < 0) {
    digitalWrite(DIRAz,LOW);
    if (-az > countAz) {
       analogWrite(PWMAz,(218-(pow(((-az)-countAz),2))));
     }
     else { analogWrite(PWMAz,255);
    }
      Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
      delay(10);
     }
  }
   while ((sqrt(alt*alt)) > countAlt || (sqrt(az*az)) > countAz);
   analogWrite(PWMAz, 255);
   analogWrite(PWMAlt, 255);
   Serial.print("Altitude Degree Change: "); Serial.print((float(countAlt))/2); Serial.print(", Azimuth Degree Change: "); Serial.println((float(countAz))/2);
}
