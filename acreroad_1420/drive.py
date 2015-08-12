"""


acreroad_1420 Drive software

Software designed to drive the 1420 MHz telescope on the roof of the
Acre Road observatory. This class interacts with "qp", the telescope
drive software by Norman Gray (https://bitbucket.org/nxg/qp) via a
serial (USB) interface.

The serial interfacing is done through pySerial.

Parameters
----------

device : str
   The name of the unix device which the drive is connected to
port : int
   The port number of the drive
simulate : bool
   A boolean flag to set the drive in simulation mode
   (the class does not connect to the controller in simulation mode)


"""

import re, datetime, time
import ConfigParser
import numpy as np
import astropy
from astropy.coordinates import SkyCoord, ICRS, EarthLocation, AltAz
import astropy.units as u
import serial
from astropy.time import Time
import threading


class Drive():

    sim = 0
    acre_road = EarthLocation(lat=55.9024278*u.deg, lon=-4.307582*u.deg, height=61*u.m)

    # Position variables
    ra = 0
    dec = 0

    az = 0
    alt = 0

    # Calibration variables

    az_home = 90.0
    el_home = -8.5

    # Operational flags
    calibrating = False
    homing = False
    ready = False

    # String formats

    com_format = re.compile("[A-Za-z]{1,2} ?([-+]?[0-9]{0,4}\.[0-9]{0,8} ?){0,6}") # general command string format
    cal_format = re.compile("[0-9]{3} [0-9]{3}") # calibration string format
    
    stat_format = re.compile(r"\b(\w+)\s*=\s*([^=]*)(?=\s+\w+\s*:|$)")
    
    def __init__(self, device, baud, timeout=None, simulate=0, calibration=None, location=None):
        """
        Software designed to drive the 1420 MHz telescope on the roof of the
        Acre Road observatory. This class interacts with "qp", the telescope
        drive software by Norman Gray (https://bitbucket.org/nxg/qp) via a
        serial (USB) interface.

        The serial interfacing is done through pySerial.

        Parameters
        ----------

        device : str
           The name of the unix device which the drive is connected to
        baud : int
           The baud-rate of the connection.
        timeout : int
           The time, in seconds, to wait before timing-out. Default is 2 seconds.
        simulate : bool
           A boolean flag to set the drive in simulation mode
           (the class does not connect to the controller in simulation mode)
        calibration : str
           The calibration figures which have been returned by a previous run of the *calibrate()* method.
           The default is `None` which forces a calibration run to be carried-out.
        location : astropy.coordinates.EarthLocation object
           The Earth location of the telescope. The default is `None`, which sets the location as Acre Road Observatory, Glasgow.

        Examples
        --------
        
        >>> from acreroad_1420 import drive
        >>> connection = drive.Drive('/dev/tty.usbserial', 9600, simulate=1)
        
        """
        config = ConfigParser.SafeConfigParser()
        config.read('settings.cfg')

        homealtaz = config.get('offsets', 'home').split()
        self.az_home, self.el_home = float(homealtaz[0]), float(homealtaz[1])

        if not location:
            observatory = config.get('observatory', 'location').split()
            location = EarthLocation(lat=float(observatory[0])*u.deg, lon=float(observatory[1])*u.deg, height=float(observatory[2])*u.m)


        self.sim = simulate
        self.timeout = timeout
        self.location = location
        # Initialise the connection
        if not self.sim: self._openconnection(device, baud)

        # Give the Arduino a chance to power-up
        time.sleep(1)
        
        self.calibrate(calibration)
        self.set_status_cadence(200)
        self.home()

        self.setTime()
        
        self.setLocation(location)

        if not self.sim:
            self.listen_thread =  threading.Thread(target=self._listener)
            self.listen_thread.daemon = True
            self.listen_thread.start()

    @property
    def current_time(self):
        """
        Return the current UTC time as an AstroPy time object.
        """
        return  Time(datetime.datetime.utcnow(), location = self.location)

    @property
    def current_time_local(self):
        """
        return the current local time
        """
        return Time( datetime.datetime.now(), location = self.location)
             
    def _openconnection(self, device, baud):
        self.ser = serial.Serial(device, baud, timeout=self.timeout)

    def _command(self, string):
        """
        Passes commands to the controller.
        """

        # Check that the command string is a string, and that it
        # matches the format required for a command string
        string = str(string)
        string = string+"\n"

        if not self.com_format.match(string):
            raise ValueError(string+" : This string doesn't have the format of a valid controller command.'")

        
        if self.sim:
            print("In simulation mode, command ignored.")
            return 1
        else:
            # Pass the command to the Arduino via pyserial
            self.ser.write(string.encode('ascii'))

            # Retrieve the return message from the controller
            #ret_line =  self.ser.readline()
            #if ret_line: return ret_line
            #else : return 1
            return 1
        
    def _listener(self):
        while True:
            line = self.ser.readline()
            self.parse(line)
            
    def parse(self, string):
        # A specific output from a function
        if string[0]==">":
            if string[1]=="S": # This is a status string of keyval pairs
                d = dict(stat_format.findall(string[2:])) #
                if d['Taz'] < 0: d['Taz'] = np.pi - d['Taz']

                self.az, self.alt = d['Taz']%(2*np.pi), d['Talt']%(0.5*np.pi)                
                return d
            if string[1]=='c': # This is the return from a calibration run
                self.calibrating=False
                print string
        # A status string
        # elif string[0]=="s":
        #     # Status strings are comma separated
        #     #print string
        #     d = string[2:].split(",")
        #     try:
        #         # We'll disable reading status strings for the moment, as they seem to be very misleading to the telescope :(
        #         try:
        #             az, alt = self._parse_floats(d[3]), self._parse_floats(d[4])
        #             if az < 0 : d[3] = str(np.pi - az)
        #             #self.az, self.alt = (az*(180/np.pi))%360, alt*(180/np.pi)
        #     except IndexError:
        #         # Sometimes (early on?) the drive appears to produce
        #         # an incomplete status string. These need to be
        #         # ignored otherwise the parser crashes the listener
        #         # process.
        #         pass
        #     #print self._parse_floats(d[3])%360
        #     return d
        elif string[0]=="a":
            if string[1]=="z" or string[1]=="l":
                # This is an azimuth or an altitude click, update the position
                d = string.split(",")
                #self.az, self.alt = self._r2d(self._parse_floats(d[2])), self._r2d(self._parse_floats(d[3]))
        elif string[0]=="!":
            # This is an error string
            print string[1:]
        elif string[0]=="#":
            # This is a comment string
            if string[1:18] == "FollowingSchedule":
                # This is a scheduler comment
                d = string.split()
                if not d[1][0] == "o":
                    # This is a pseudo-status string
                    self.az, self.alt = self._r2d(self._parse_floats(d[2])), self._r2d(self._parse_floats(d[3]))
            pass
        #else: print string

    def slewSuccess(self,targetPos):
        """
        """
        (cx,cy) = self.status()['az'], self.status()['alt']
        realPos = SkyCoord(AltAz(cx*u.deg,cy*u.deg,obstime=self.current_time,location=self.location))
        d = 3
        
        if targetPos.separation(realPos).value <= d:
            #print("Finished slewing to " + str(self.getCurrentPos()))
            return True
        else:
            return False
            
    def _r2d(self, radians):
        """
        Converts radians to degrees.
        """
        degrees = radians*(180/np.pi)
        if degrees < 0 : degrees += 360
        return degrees%360
        
    def _d2r(self, degrees):
        """
        Converts degrees to radians.
        """
        radians =  degrees*(np.pi/180)
        if radians < 0 : radians += (2*np.pi)
        return radians%(2*np.pi)

    def _parse_floats(self, string):
        """Parses the float outputs from the controller in a robust way which
        allows for the exponent to be a floating-point numberm, which
        is not supported by Python.

        Parameters
        ----------
        string : str
           A string containing the float which needs to be cast.

        Returns
        -------
        float
           A float which is in the correct format for Python.
        """
        parts = string.split('e')
        if len(parts)==2:
            return float(parts[0]) * 10**float(parts[1])
        else:
            return float(parts[0])

    def panic(self):
        """
        Stops the telescope drives.
        """
        return self._command("x")
            
    def set_status_cadence(self, interval):
        """
        Sets the cadence of the status messages from the controller.
        """
        return self._command("s {}".format(int(interval)))

    def calibrate(self, values=None):

        """
        Carries-out a calibration run, returning two numbers which are offsets, or sets the calibration if known values are provided.

        Parameters
        ----------

        values : str
           The calibration values produced by a previous calibration run of the telescope, provided in the format "nnn nnn"

        """
        if self.sim: return ">c 000 000"
        if values:                      
            # Check the format of the values string.
            if self.cal_format.match(values):
                return self._command("c "+values)
        else:
            self.calibrating=True
            return self._command("c")
        pass

    def setTime(self):
        """
        Sets the time on the drive controller's clock to the current system time.

        """
        time = datetime.datetime.utcnow()

        command_str = "T {} {} {} {} {} {:.4f}".format(time.year, time.month, time.day, time.hour, time.minute, time.second)

        return self._command(command_str)

    def setLocation(self, location=None, dlat=0, dlon=0, azimuth=90.0, altitude=3.0):
        """
        Sets the location of the telescope.

        Parameters
        ----------
        location : astropy.coordinates.EarthLocation object
           The observatory location
        azimuth : float
           The azimuth location in radians of the home position
        altitude : float
           The altitude location in radians of the home position
        """
        if not location:
            # Assume we're at Acre Road, in Glasgow
            location = self.acre_road

        latitude  = location.latitude.value * (180/np.pi)
        longitude = location.longitude.value * (180/np.pi)

        azimuth = azimuth*(np.pi/180)
        altitude = altitude*(np.pi/180)

        # Construct the command
        command_str = "O {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f}".format(latitude, longitude, dlat, dlon, azimuth, altitude)
        
        return self._command(command_str)

    def goto(self, skycoord, track=True):
        """
        Moves the telescope to point at a given sky location, and then commands the drive to track the point.

        Parameters
        ----------
        skycoord : astropy.SkyCoord object
           An astropy SkyCoord object which contains the sky location to slew to.
           This can also be a list of locations which the telescope will slew to sequentially. 

        """

        if not type(skycoord)==astropy.coordinates.sky_coordinate.SkyCoord:
            raise ValueError("The sky coordinates provided aren't an astropy SkyCoord object!'")

        # To do : We need to make sure that this behaves nicely with a
        # list of coordinates as well as single ones.

        time = Time.now()

        skycoord = skycoord.transform_to(AltAz(obstime=time, location=self.location))
        self.status()
        # construct a command string
        command_str = "gh {0.az.radian:.2f} {0.alt.radian:.2f}".format(skycoord)
        # pass the slew-to command to the controller
        if self._command(command_str):
            if track:
                command_str = "q"
                self._command(command_str)
                command_str = "ts"
                self._command(command_str)
            while not self.slewSuccess(skycoord):
                self.slewing = True
            else:
                self.slewing = False
        else:
            raise ControllerException("The telescope has failed to slew to the requested location")

    def home(self):
        """
        Slews the telescope to the home position.

        
        """
        self.homing = True
        command_str = "gH"
        self._command(command_str)
        home_pos = SkyCoord(AltAz(self.az_home*u.deg,self.el_home*u.deg,obstime=self.current_time,location=self.location))
        while not self.slewSuccess(home_pos):
            self.homing = False

    def stow(self):
        """
        Slews the telescope to the stowing position (pointed at the zenith)
        """
        zenith = 90*(np.pi/180)
        command_str = "gh 2.0 "+str(zenith)
        return self._command(command_str)


    def status(self):
        """
        Returns a dictionary describing the status of the telescope (e.g. its location).

        Returns
        -------
        dict
           A dictionary containing the right ascension, declination, altitude, and azimuth of the telescope.

        Examples
        --------

        >>> from astropy.coordinates import SkyCoord
        >>> from astropy.coordinates import ICRS, 
        >>> c = SkyCoord(frame="galactic", l="1h12m43.2s", b="+1d12m43s")
        >>> self.connection.goto(c)
        >>> ra = self.connection.status()['ra'].value
        
        """
        command_str = "S"
        #self._command(command_str)
        return {'ra':self.ra, 'dec': self.dec, 'alt':self.alt, 'az':self.az}


class ControllerException(Exception):
    pass
