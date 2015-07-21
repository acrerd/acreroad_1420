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

class Drive():

    sim = 0

    # String formats

    com_format = re.compile("[A-Za-z]{1,2} ? ([-+]?[0-9]{0,4}\.[0-9]{0,8} ?){0,6}") # general command string format
    cal_format = re.compile("[0-9]{3} [0-9]{3}") # calibration string format
    

    
    def __init__(self, device, port, simulate):
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

    def setLocation(self, latitude=None, longitude=None, dlat=0, dlon=0):
        """
        Sets the location of the telescope.

        Parameters
        ----------
        latitude : float
           The latitude of the telescope (in degrees)
        longitude : float
           The longitude of the telescope (in degrees)
        """
        if not latitude and not longitude:
            # Assume we're at Acre Road, in Glasgow
            latitude, longitude = 55.9024278, -4.307582
        elif not latitude or not longitude:
            raise ValueError("Cannot work out location from information provided!")

        # Construct the command
        command_str = "T {} {} {} {}".format(latitude, longitude, dlat, dlon)
        print command_str
        return self._command(command_str)

    def goto(self, skycoord):
        """
        Moves the telescope to point at a given sky location.

        Parameters
        ----------
        skycoord : astropy.SkyCoord object
           An astropy SkyCoord object which contains the sky location to slew to. This can also be a list of locations which the telescope will slew to sequentially. 

        """
        pass
        
    