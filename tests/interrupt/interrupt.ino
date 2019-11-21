int pin = 13;
volatile int count = 0;
volatile unsigned long  lastpulse = 0;

void setup()
{
  attachInterrupt(pin, reed, FALLING);
  Serial.begin(9600);
}

void loop()
{
    Serial.println(count);
      delay(100);
}

void reed()
{
  unsigned long currentMillis = millis();
 if ((unsigned long)(currentMillis - lastpulse) >= 60) // only increment if more than 60ms since last pulse
   {
     count = count+1;
   }
  lastpulse = millis();
}
