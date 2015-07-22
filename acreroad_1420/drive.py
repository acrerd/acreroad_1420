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

class Drive():

    sim = 0
    acre_road = EarthLocation(lat=55.9024278*u.deg, lon=-4.307582*u.deg, height=61*u.m)

    # String formats

    com_format = re.compile("[A-Za-z]{1,2} ?([-+]?[0-9]{0,4}\.[0-9]{0,8} ?){0,6}") # general command string format
    cal_format = re.compile("[0-9]{3} [0-9]{3}") # calibration string format
    

    
    def __init__(self, device, port, simulate):
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
        port : int
           The port number of the drive
        simulate : bool
           A boolean flag to set the drive in simulation mode
           (the class does not connect to the controller in simulation mode)

        """
        self.sim = simulate
        pass

    def _command(self, string):
        """
        Passes commands to the controller.
        """

        # Check that the command string is a string, and that it
        # matches the format required for a command string
        string = str(string)

        if not self.com_format.match(string):
            raise ValueError(string+" : This string doesn't have the format of a valid controller command.'")

        
        if self.sim:
            print("In simulation mode, command ignored.")
            return 1
        
        
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

        command_str = "t {} {} {} {} {} {}".format(time.year, time.month, time.day, time.hour, time.minute, time.second)

        return self._command(command_str)

    def setLocation(self, location=None, dlat=0, dlon=0):
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
        command_str = "T {} {} {} {}".format(latitude, longitude, dlat, dlon)
        return self._command(command_str)

    def goto(self, skycoord):
        """
        Moves the telescope to point at a given sky location, and then commands the drive to track the point.

        Parameters
        ----------
        skycoord : astropy.SkyCoord object
           An astropy SkyCoord object which contains the sky location to slew to. This can also be a list of locations which the telescope will slew to sequentially. 

        """

        if not type(skycoord)==astropy.coordinates.sky_coordinate.SkyCoord:
            raise ValueError("The sky coordinates provided aren't an astropy SkyCoord object!'")

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
            
            # If the command completes then set the controller to track the object
            command_str = "ts"
            return self._command(command_str)
        else:
            raise ControllerError("The telescope has failed to slew to the requested location")
        
    