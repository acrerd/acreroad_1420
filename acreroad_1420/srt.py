import time, astropy
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from PyQt4 import QtGui,QtCore
from drive import Drive

class Status:
    INIT = 0
    SLEWING = 1
    PARKED = 2
    CALIBRATING = 3
    READY = 4
    TRACKING = 5

class CoordinateSystem:
    RADEC = 0
    AZEL = 1
    GAL = 3

class Mode:
    LIVE = 0
    SIM = 1

class SRT():   
    def __init__(self,mode,device,calibrationSpeeds):
        baud = 9600
        if mode == Mode.SIM:
            self.drive = Drive(device,baud,simulate=1,calibration=calibrationSpeeds)
        elif mode == Mode.LIVE:
            self.drive = Drive(device,baud,simulate=0,calibration=calibrationSpeeds)
        self.pos = self.azalt()
        self.location = self.drive.location  #TODO - use this
        self.status = Status.INIT
        self.mode = mode

    def getCurrentPos(self):
        """
        Returns current position in azalt.
        """
        return self.pos
        
    def setCurrentPos(self, pos):
        self.pos = pos
        
    def getMode(self):
        return self.mode

    def setMode(self,mode):
        self.mode = mode

    def azalt(self):
        """
        Returns the azimuth and altitude of the SRT by calling the status() method of the drive class.
        """
        status = self.drive.status()
        az,alt = status['az'],status['alt']
        #print("status " + "%f %f" % (az,alt))
        return (az,alt)

    def radec(self):
        """
        Returns the right ascention and declination of the SRT by calling the status() method of the drive class.
        """
        status = self.drive.status()
        ra,dec = status['ra'],status['dec']
        return (ra,dec)

    def galactic(self):
        """
        """
        return (0.00,0.00)


    def stow(self):
        """
        A wrapper function for Drive.stow().
        """
        self.setStatus(Status.SLEWING)
        if self.mode == Mode.SIM:
            self.slew((0,90))
        elif self.mode == Mode.LIVE:
            self.drive.stow()

    def home(self):
        """
        A wrapper function for Drive.home().
        """
        self.setStatus(Status.SLEWING)
        if self.mode == Mode.SIM:
            self.slew((90,0))
        elif self.mode== Mode.LIVE:
            self.drive.home()

    def calibrate(self):
        """
        A wrapper function for Drive.calibrate().
        """
        if self.mode == Mode.SIM:
            print("Calibration only works in live mode.")
        elif self.mode == Mode.LIVE:
            self.setStatus(Status.CALIBRATING)
            self.drive.calibrate()

    def slew(self,pos):
        """
        Slews to position pos in degrees.
        """
        delay = 0.05
        self.status = Status.SLEWING
        if self.mode == Mode.SIM:
            print("Slewing in sim mode.")
            (xf,yf) = pos # target position in degrees
            x = int(xf)
            y = int(yf)
            (cxf,cyf) = self.pos # current position in degrees
            cx = int(cxf)
            cy = int(cyf)
            if x < cx:
                for i in reversed(range(x,cx)):
                    self.setCurrentPos((i,cy))
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
            elif x > cx:
                for i in range(cx,x+1):
                    self.setCurrentPos((i,cy))
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
            if y < cy:
                for i in reversed(range(y,cy)):
                    self.setCurrentPos((x,i))
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
            elif y > cy:
                for i in range(cy,y+1):
                    self.setCurrentPos((x,i))
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
        else:
            # This is where live code goes
            # remember self.getCurrentPos() is now in degrees in azalt - NOT pixel coordinates.
            print("Slewing in live mode.")
            (x,y) = pos # target - mouse click position in degrees
            (cx,cy) = self.pos # current position in degrees.
            print("Target Pos: (" + str(x) + "," + str(y) + ")")
            print("Current Pos: (" + str(cx) + "," + str(cy) + ")")
            # construct a SkyCoord in correct coordinate frame.
            # TODO: fix this -- drive.location
            acreRoadAstropy = self.location
            now = Time(time.time(),format='unix')
            altazframe = AltAz(x*u.deg,y*u.deg,obstime=now,location=acreRoadAstropy)
            skycoordazel = SkyCoord(altazframe)        
            self.drive.goto(skycoordazel,track=False)

        
    def slewSuccess(self,targetPos):
        """
        """
        (tx,ty) = targetPos
        (cx,cy) = self.pos
        d = 1
        #print("Target: %f %f" % (tx,ty))
        #print("Current: %f %f" % (cx,cy))
        #print(abs(tx-cx),abs(ty-cy))
        if (abs(tx-cx) <= d) and (abs(ty-cy) <= d):
            #print("Finished slewing to " + str(self.getCurrentPos()))
            return True
        else:
            return False

    def getStatus(self):
        return self.status

    def setStatus(self,status):
        self.status = status

    def track(self,src):
        """
        The SRT will follow the source as it move across the sky.
        """
        if self.mode == Mode.SIM:
            #print("Tracking " + src.getName())
            pos = src.getPos()
            self.slew(pos)
            self.status = Status.TRACKING
        else:
            # this is where the live code goes.
            pass
        
       
