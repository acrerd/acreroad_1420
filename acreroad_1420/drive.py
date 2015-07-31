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

import re, datetime

import astropy
from astropy.coordinates import SkyCoord, ICRS, EarthLocation
import astropy.units as u
import serial

class Drive():

    sim = 0
    acre_road = EarthLocation(lat=55.9024278*u.deg, lon=-4.307582*u.deg, height=61*u.m)

    # Position variables
    ra = 0
    dec = 0

    # String formats

    com_format = re.compile("[A-Za-z]{1,2} ?([-+]?[0-9]{0,4}\.[0-9]{0,8} ?){0,6}") # general command string format
    cal_format = re.compile("[0-9]{3} [0-9]{3}") # calibration string format
    

    
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
        self.sim = simulate
        self.timeout = timeout
        # Initialise the connection
        if not self.sim: self._openconnection(device, baud)
        
        self.calibrate(calibration)
        self.setTime()
        
        self.setLocation(location)
        pass

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
            ret_line =  self.ser.readline()
            if ret_line: return ret_line
            else : return 1
        
        
    def calibrate(self, values=None):
        """
        Carries-out a calibration run, returning two numbers which are offsets, or sets the calibration if known values are provided.

        Parameters
        ----------

        values : str
           The calibration values produced by a previous calibration run of the telescope, provided in the format "nnn nnn"

        """
        if values:
            # Check the format of the values string.
            if self.cal_format.match(values):
                return self._command("c "+values)
        if self.sim: return ">c 000 000"
        pass

    def setTime(self):
        """
        Sets the time on the drive controller's clock to the current system time.

        """
        time = datetime.datetime.utcnow()

        command_str = "T {} {} {} {} {} {}".format(time.year, time.month, time.day, time.hour, time.minute, time.second)

        return self._command(command_str)

    def setLocation(self, location=None, dlat=0, dlon=0, azimuth=90, altitude=-6):
        """
        Sets the location of the telescope.

        Parameters
        ----------
        location : astropy.coordinates.EarthLocation object
        """
        if not location:
            # Assume we're at Acre Road, in Glasgow
            location = self.acre_road

        latitude  = location.latitude
        longitude = location.longitude    

        # Construct the command
        command_str = "O {} {} {} {} {} {}".format(latitude, longitude, dlat, dlon, azimuth, altitude)
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

        # We need to make sure that we send RA and DEC values to the
        # controller (it is theoretically possible to do ALTAZ too,
        # but let's start simple, eh?')

        skycoord = skycoord.transform_to(frame=ICRS)
        ra  = skycoord.ra
        dec = skycoord.dec
        
        # construct a command string
        command_str = "gE {} {}".format(ra, dec)
        # pass the slew-to command to the controller
        if self._command(command_str):
            # We need to do more here than just check the command has
            # passed successfully; we need to check the telescope is
            # (or thinks it is) pointing where we asked.
            if self.sim:
                self.ra  = ra
                self.dec = dec
            
            # If the command completes then set the controller to track the object
            if track:    
                command_str = "ts"
                return self._command(command_str)
            else: return 1
        else:
            raise ControllerException("The telescope has failed to slew to the requested location")

    def home(self):
        """
        Slews the telescope to the home position.

        
        """
        command_str = "gH"
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
        return {'ra':self.ra, 'dec': self.dec, 'alt':0, 'az':0}


class ControllerException(Exception):
    pass