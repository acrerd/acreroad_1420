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

import time
import re, datetime, time
from . import CONFIGURATION as config
import numpy as np
import astropy
from astropy.coordinates import SkyCoord, ICRS, EarthLocation, AltAz
import astropy.units as u
import serial
from astropy.time import Time
import threading
from os.path import expanduser, isfile, join
import os.path

import logging



class Drive():

    # The vocabulary from the qt package.
    # This should probably be moved to a file in its own right to help
    # make the drive more generic
    vocabulary = {
        "DRIVE_UP"  : "gU",
        "DRIVE_DOWN": "gD",
        "DRIVE_EAST": "gE",
        "DRIVE_WEST": "gW",
        "DRIVE_HOME": "gH",
        "SET_SPEED" : "ta {}",
        "CALIBRATE" : "c {:f} {:f}",
        "STOP"      : "x",
        "STOW"      : "X",
        "SET_TIME"  : "T {:d} {:d} {:d} {:d} {:d} {:d}",
        # status command, s, not currently implemented this way
        "STATUS_CAD": "s {:d}",
        "GOTO_HOR" : "gh {:f} {:f}",
        "GOTO_EQ"  : "ge {:f} {:f}",
        # Nudges
        "NUDGE_UP"  : "nu {:f}",
        "NUDGE_DOWN": "nd {:f}",
        "NUDGE_WEST": "nw {:f}",
        "NUDGE_EAST": "ne {:f}",
        # Setup
        "SETUP"     : "O {:f} {:f} {:f} {:f} {:f} {:f} {:f}",
        # QUEUE
        "QUEUE"     : "q",
        # TRACKING
        # disabled as of qp v0.7b2
        #"TRACK_SID"  : "ts",
        #"TRACK_RA"   : "ts {:f}",
        "TRACK_AZ"    : "ta {:f}",
        }
    
    MAX_SPEED = 0.5

    sim = 0
    acre_road = EarthLocation(lat=55.9024278*u.deg, lon=-4.307582*u.deg, height=61*u.m)

    # Position variables
    ra = 0
    dec = 0

    az = 26
    alt = 3

    # Calibration variables

    #az_home = 90.0
    #el_home = -8.5

    # Operational flags
    calibrating = False
    homing = False
    ready = False
    tracking = False
    slewing = False

    # String formats

    com_format = re.compile("[A-Za-z]{1,2} ?([-+]?[0-9]{0,4}\.[0-9]{0,8} ?){0,6}") # general command string format
    cal_format = re.compile("[0-9]{3} [0-9]{3}") # calibration string format
    
    #stat_format = re.compile(r"\b(\w+)\s*=\s*([^=]*)(?=\s+\w+\s*:|$)")
    stat_format = re.compile(r"(?=\s+)([\w_]+)\s*=\s*([\d_:\.T]+)")
    
    def __init__(self, device=None, baud=None, timeout=3, simulate=0, calibration=None, location=None, persist=True, homeonstart=True):
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
        
        >> from acreroad_1420 import drive
        >>> connection = drive.Drive('/dev/tty.usbserial', 9600, simulate=1)
        
        """


        self.config = config

        # Setup the logger
        #
        logfile = config.get('logs', 'logfile')
        logging.basicConfig(filename=logfile,
                            format='[%(levelname)s] [%(asctime)s] [%(message)s]',
                            level=logging.DEBUG)
        
        #
        # Fetch the sky position which corresponds to the 'home' position of the telescope
        #
            
        homealtaz = config.get('offsets', 'home').split()
        self.az_home, self.el_home = float(homealtaz[0]), float(homealtaz[1])

        # Add a dirty hack to easily calibrate the telescope in software
            
        absaltaz = config.get('offsets', 'absolute').split()
        self.az_abs, self.el_abs = float(absaltaz[0]), float(absaltaz[1])


        #
        # Pull the location of the telesope in from the configuration file if it isn't given as an argument to the
        # class initiator.
        #
        
        if not location:
            logging.info("The observatory location was not provided, so it will be loaded from the config file")
            observatory = config.get('observatory', 'location').split()
            location = EarthLocation(lat=float(observatory[0])*u.deg, lon=float(observatory[1])*u.deg, height=float(observatory[2])*u.m)


        self.sim = self.simulate = simulate
        self.timeout = timeout
        self.location = location

        self.targetPos = SkyCoord(AltAz(self.az_abs*u.deg,self.el_abs*u.deg,obstime=self.current_time,location=self.location))

        #
        # Initialise the connection to the arduino Note that this can
        # be complicated by the ability of the device name to change
        # when disconnected and reconnected, so a search is
        # required. This is now handled by the `_openconnection()`
        # method.
        if not baud:
            # Get the target baudrate from the config file
            baud = config.get("arduino", "baud")
        
        if not device:
            device = config.get('arduino','dev')
        
        if not self.sim:
            self._openconnection(device, baud)
            logging.info("Drive controller connected.")

        
        # Give the Arduino a chance to power-up
        time.sleep(1)

        if not calibration:
            try: 
                calibration = config.get('calibration', 'speeds')
            except: pass

        self.span = float(config.get("offsets", "span"))

        self.calibration = calibration
        self.calibrate(calibration)
        #self.calibrate()

        # Set the format we want to see status strings produced in; we just want azimuth and altitude.
        #self.set_status_cadence(200)
        #self.set_status_message('za')
        self.target = (self.az_home, self.el_home)

        # Set the Arduino clock
        self.setTime()

        # Tell the Arduino where it is
        #self.setLocation(location)

        # Home on start
        logging.info("Homing the telescope.")
        if homeonstart:
            self.home()
        
        if not self.sim:
            self.listen_thread =  threading.Thread(target=self._listener)
            self.listen_thread.daemon = True
            self.listen_thread.start()

        self.ready = True

        self.track()
        self.stop_track()


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
        from serial import SerialException
        import serial
        try:
            self.ser = serial.Serial(device, baud, timeout=self.timeout)
            logging.info("Drive connected on {} at {} baud".format(device, baud))
        except SerialException:
            # The arduino might be connected, but it's not at that
            # device address, so let's have a look around.
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                if "ACM" in p[0]:
                    device = p[0]
                    break
            self._openconnection(device, baud)

    def _command(self, string):
        """
        Passes commands to the controller.
        """

        # Check that the command string is a string, and that it
        # matches the format required for a command string
        string = str(string)
        string = string+"\n"

        if not self.com_format.match(string):
            logging.error("Invalid command rejected: {}".format(string))
            raise ValueError(string+" : This string doesn't have the format of a valid controller command.'")

        
        if self.sim:
            print("In simulation mode, command ignored.")
            return 1
        else:
            # Pass the command to the Arduino via pyserial
            logging.debug("Command: {}".format(string))
            self.ser.write(string.encode('ascii'))
            return 1
        
    def _listener(self):
        while True:
            try:
                line = self.ser.readline()
                self.parse(line)
            except Exception as e:
                print str(e)
                logging.error("Parser error, continuing. \n {}".format(line))
        time.sleep(0.5)
        return

    def _stat_update(self, az, alt):
        """
        Update the internal record of the telescope's position.
        This is normally parsed from one of the status strings by the parser 
        method.

        Parameters
        ----------
        az : float, degrees
           The azimuth of the telescope.
           This must be provided in degrees.
        alt : float, degrees
           The altitude of the telescope.
           This must also be provided in degrees.
        
        Returns
        -------
        None
        
        Notes
        -----
        Due to oddities in how the telescope seems to be reporting the 
        altitude, this function currently calculates the appropriate modulus
        for the altitude if it is greater than 90 deg.
        
        This should really be looked into more carefully.

        * TODO Investigate erratic altitude reports.
        """
        
        # Check that the values are within an acceptable range
        # Otherwise modulate them.
        if az > 360 : az = az % 360
        if alt > 90 : alt = alt % 90

        self.az, self.alt = az, alt
            
    def parse(self, string):
        #print string
        # Ignore empty lines
        if len(string)<1: return 0
        logging.debug(string)
        # A specific output from a function
        if string[0]==">":
            #print string
            if string[1]=="S": # This is a status string of keyval pairs
                # This currently seems to be broken, so pass
                pass
                # print("string", string[2:])
                d = string[2:].split()
                out = {}
                for field in d:
                    key, val = field.split("=")
                    out[key] = val
                #print("d", out)
                try:
                    #print "Status string"
                    az, alt = out['Taz'], out['Talt']
                except KeyError:
                    logging.error('Key missing from the status output {}'.format(out))
                return out
            if string[1:3] == "g E":
                # Telescope has reached an endstop and will need to be homed before continuing.
                logging.info("The telescope appears to have hit an end-stop.")
                #self.home()
                #logging.info("Rehoming the telescope.")
                #self._command(self.vocabulary["QUEUE"])
                #logging.info("After re-homing the telescope will attempt to move to the requested location again.")
                #self.goto(self.target)
            if string[1:4] == "g A":
                # This is the flag confirming that the telescope has reached the destination.
                self.slewing = False
                logging.info("The telescope has reached {}".format(string[3:]))
            if string[1]=='c':
                # This is the return from a calibration run
                logging.info("Calibration completed. New values are {}".format(string[2:]))
                self.calibrating=False
                self.config.set('offsets','calibration',string[2:])
                self.calibration = string[2:]
                #print string
            else:
                logging.info(string[1:])

        # A status string
        elif string[0]=="s" and len(string)>1:
            # Status strings are comma separated
            d = string[2:].strip('\n').split(",")
            if len(d) > 3: return
            try:
                #try:
                az, alt = self._parse_floats(d[1]), self._parse_floats(d[2])
                #az = np.pi - az
                
                self._stat_update( self._r2d(az), self._r2d(alt) )
            except:
                logging.error(d)
                logging.info("{} az, {} alt".format(az, alt))
                if len(d)<3: return
                az, alt = self._parse_floats(d[1]), self._parse_floats(d[2])
                #print az, type(az)
                #print alt, self._r2d(az), az
                self._stat_update( self._r2d(az), self._r2d(alt) )
                #    print self._parse_floats(d[1]), self._parse_floats(d[2])

                pass
            #except IndexError:
                # Sometimes (early on?) the drive appears to produce
                # an incomplete status string. These need to be
                # ignored otherwise the parser crashes the listener
                # process.
            #    pass
            return d
        elif string[0]=="a":            
            if string[1]=="z" or string[1]=="l":
                # This is an azimuth or an altitude click, update the position
                d = string.split(",")
                #print string, d
                #print d
                self._stat_update(self._r2d(self._parse_floats(d[3])), self._r2d(self._parse_floats(d[4])))
        elif string[0]=="!":
            # This is an error string
            logging.error(string[1:])
            print "Error: {}".format(string[1:])
        elif string[0]=="#":
            logging.info(string[1:])
            pass
            #print string
        #     # This is a comment string
        #     if string[1:18] == "FollowingSchedule":
        #         # This is a scheduler comment
        #         d = string.split()
        #         if not d[1][0] == "o":
        #             pass

        #    pass
        else: pass
        

    def slewSuccess(self):
        """
        Checks if the slew has completed. This /should/ now be 
        entirely handled by qp, and all we need to do is to 
        check that the slewing flag is false.
        """
        if type(self.targetPos) is tuple:
            (cx, cy) = self.targetPos
            #if cx > 90.0: cx -= (cx - 90) 
            self.targetPos = SkyCoord(AltAz(cx*u.deg,cy*u.deg,obstime=self.current_time,location=self.location))
            
        cx,cy = self.status()['az'], self.status()['alt']
        print cx, cy
        self.realPos = SkyCoord(AltAz(az=cx*u.deg,alt=cy*u.deg,obstime=self.current_time,location=self.location))
        d = 0.5 * u.degree

        if self.targetPos.separation(self.realPos) < d:
            return True
        else:
            return False
            
    def _r2d(self, radians):
        """
        Converts radians to degrees.
        """
        degrees = radians*(180/np.pi)
        #if degrees < 0 : 180 - degrees 
        return degrees%360
        
    def _d2r(self, degrees):
        """
        Converts degrees to radians.
        """
        radians =  degrees*(np.pi/180)
        if radians < 0 : radians = radians #(np.pi-radians)
        return radians%(2*np.pi)

    def _parse_floats(self, string):
        """
        Parses the float outputs from the controller in a robust way which
        allows for the exponent to be a floating-point number, which
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
        if string == '0e0':
            return 0.0
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

    def set_speed(self, speed):
        """
        Set the speed of the drive in radians / second.

        Parameters
        ----------
        speed : float [rad/sec]
           The physical angular speed which the motor should attempt to
           drive at.
        """
        command = self.vocabulary['SET_SPEED']
        if speed > self.MAX_SPEED: 
            print("{} is greater than the maximum speed ({})".format(speed, self.MAX_SPEED))
            return
        else:
            # The command can have the speed added using a format command
            return self._command(command.format(speed))
        

    def move(self, direction):
        """
        Start moving the telescope in a specified direction.

        Parameters
        ----------
        direction : {left, right, up, down}
           Direction to move the telescope.
        """
        directions = ["west", "east", "up", "down"]
        if direction not in directions:
            print("Unknown direction provided.")
            return None
        else:
            commands = {"east": "DRIVE_EAST", "west": "DRIVE_WEST",
                        "up" : "DRIVE_UP", "down": "DRIVE_DOWN"}
            # Find the command which corresponds to the correct
            # vocabulary command
            command = commands[direction]
            if command in self.vocabulary:
                print(self.vocabulary[command])
                return self._command(self.vocabulary[command])
    
    def change_offset(self, direction, amount):
        """
        Change the software-defined offsets for this script (and not for qt).

        Parameters
        ----------
        direction : str {"azimuth", "altitude"}
           The axis along which the correction must be made.
        amount : float
           The change of correction to be applied, in degrees.
        """
        directions = ['azimuth', 'altitude']
        if direction not in directions:
            print("I do not understand the direction {}".format(direction))
        else:
            if direction == directions[0]: # azimuth
                self.az_abs += amount
            elif direction == directions[1]: #altitude
                self.el_abs += amount
        # Set the new calibration on the motor
        print("New calibration is {}az {}alt".format(self.az_home, self.el_home))
        # Write the new calibration to the config file
        self.config.set('offsets','absolute',"{} {}".format(self.az_home, self.el_home))
        return
        #return self._command(self.vocabulary['CALIBRATE'].format(self.az_home, self.el_home))
        
        

    def set_status_cadence(self, interval):
        """
        Sets the cadence of the status messages from the controller.
        """
        return self._command("s {}".format(int(interval)))

    def set_status_message(self, message):
        """
        Determines the output of the status messages produced by the controller.
        """
        return self._command("s {}".format(message))

    def calibrate(self, values=None):

        """
        Carries-out a calibration run, returning two numbers which are offsets, or sets the calibration if known values are provided.

        Parameters
        ----------

        values : str
           The calibration values produced by a previous calibration run of the telescope, provided in the format "nnn nnn"

        """
        if self.sim:
            return ">c 000 000"
        if values:                      
            # Check the format of the values string.
            if self.cal_format.match(values):
                return self._command(self.vocabulary["CALIBRATE"].format(values[0], values[1]))
                #return self._command("c "+values)
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

    def setLocation(self, location=None, dlat=0, dlon=0, azimuth=None, altitude=None):
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

        azimuth, altitude = self.az_home, self.el_home

        if not location:
            # Assume we're at Acre Road, in Glasgow
            location = self.acre_road

        latitude  = location.latitude.value #* (180/np.pi)
        longitude = location.longitude.value #* (180/np.pi)

        azimuth = azimuth*(np.pi/180)
        altitude = altitude*(np.pi/180)

        # Construct the command
        command_str = "O {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f}".format(latitude, longitude, dlat, dlon, azimuth, altitude, self.span)
        
        return self._command(command_str)

    def goto(self, skycoord, track=False):
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

        self.target = skycoord

        # Stop any ongoing tracking
        self.stop_track()
        self.slewing = True

        # To do : We need to make sure that this behaves nicely with a
        # list of coordinates as well as single ones.
        
        time = Time.now()

        skycoord = skycoord.transform_to(AltAz(obstime=time, location=self.location))

        logging.info("Going to {0.az} {0.alt}".format(skycoord))

        self.target = skycoord
        self.status()
        # construct a command string
        #self._command(self.vocabulary["QUEUE"])
        command_str = "gh {0.az.radian:.2f} {0.alt.radian:.2f}".format(skycoord)
        # pass the slew-to command to the controller
        if self._command(command_str):

            print "Command received."
            self.slewing = True
        else:
            self.slewing = True
            raise ControllerException("The telescope has failed to slew to the requested location")

        if track:
            self.track()
        
    def track(self, interval = 60):
        """Make the drive track an object.

        Notes
        -----

        At the moment qp can't handle tracking correctly, and so this
        is implemented in this module in a slightly less graceful
        manner. The position of the drive is checked at regular
        intervals, and is corrected to keep an object within the beam
        of the telescope, by simply driving forwards.

        This allows a little more flexibility than keeping the drive
        running continuously at slow speed, as we can track faster
        moving objects, e.g. the sun, this way. However, tracking a
        very fast-moving object is probably impractical (e.g. a
        satellite), and would require something more robust.
        """
        
        #if tracking:
        #     self.tracking = True
        #     command_str = "q"
        #     self._command(command_str)
        #     command_str = "ts"
        #     self._command(command_str)
        # else: 
        #     self.tracking=False
        #     command_str = "q"
        #     self._command(command_str)
        #     command_str = "ts 0.0"
        #     self._command(command_str)

        # Set the tracking flag
        self.tracking = True

        # Set-up the threaded tracking process as a timer

        self.tracking_thread = threading.Timer(self._tracking, interval)
        self.tracking_thread.start()

    def stop_track(self):
        """
        Stop on-going tracking.
        """
        
        self.tracking_thread.cancel()
        self.tracking = False
            
    def _tracking(self):
        self.tracking_thread.start()

    def stop_track(self):
        """
        Stop on-going tracking.
        """
        
        self.tracking_thread.cancel()
        self.tracking = False
    
    def _tracking(self):
        """This is the function which actually carries out the heavy lifting
        required for the telescope tracking to work. It's not all that
        sophisticated.
        """

        # Do not track if the telescope is still slewing
        if not self.slewing:
            self.goto(self.target)
        

    def home(self):
        """
        Slews the telescope to the home position.

        
        """
        self.homing = True
        command_str = "gH"
        self._command(command_str)
        home_pos = SkyCoord(AltAz(alt=self.el_home*u.deg,
                                  az=self.az_home*u.deg,obstime=self.current_time,location=self.location))
        self.target = home_pos

    def stow(self):
        """
        Slews the telescope to the stowing position (pointed at the zenith)
        """
        zenith = self._d2r(89)
        command_str = "gh 1.6 1.5"#+str(zenith)
        self.target = (0.0, 90.0)
        return self._command(self.vocabulary["STOW"])
        

    def skycoord(self):
        cx,cy = self.status()['az'], self.status()['alt']
        realPos = SkyCoord(AltAz(az=cx*u.deg, alt=cy*u.deg,
                                 obstime=self.current_time,
                                 location=self.location))
        return realPos

    @property
    def current_position(self):
        return self.skycoord()
    

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
        #time.sleep(0.1)
        return {'ra':self.ra, 'dec': self.dec, 'alt':self.alt, 'az':self.az}


class ControllerException(Exception):
    pass
