import time, astropy
from PyQt4 import QtGui
from drive import Drive

class Status:
    INIT = 0
    SLEWING = 1
    PARKED = 2
    CALIBRATING = 3
    READY = 4

class CoordinateSystem:
    RADEC = 0
    AZEL = 1
    GAL = 3

class Mode:
    LIVE = 0
    SIM = 1

class SRT():
   
    def __init__(self,mode):
        device = ""
        baud = 9600
        self.drive = Drive(device,baud,simulate=1)
        self.pos = azalt()
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
        status = self.drive.status()
        ra,dec = status['ra'],status['dec']
        az,alt = status['az'],status['alt']
        return (az,alt)

    def radec(self):
        status = self.drive.status()
        ra,dec = status['ra'],status['dec']
        az,alt = status['az'],status['alt']
        return (ra,dec)

    def calibrate():
        pass

    def slew(self,skymap,pos):
        """Slews to position pos in pixel coordinates."""
        delay = 0.01
        self.status = Status.SLEWING
        if self.mode == Mode.SIM:
            print("Slewing in sim mode.")
            (x,y) = pos
            (cx,cy) = self.pos
            print("Target Pos: (" + str(skymap.pixelToDegreeX(x)) + "," + str(skymap.pixelToDegreeY(y)) + ")")
            print("Current Pos: (" + str(skymap.pixelToDegreeX(cx)) + "," + str(skymap.pixelToDegreeY(cy)) + ")")
            if x < cx:
                for i in reversed(range(x,cx)):
                    self.setCurrentPos((i,cy))
                    skymap.setCurrentPos((i,cy))
                    skymap.update()
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
            elif x > cx:
                for i in range(cx,x+1):
                    self.setCurrentPos((i,cy))
                    skymap.setCurrentPos((i,cy))
                    skymap.update()
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
            if y < cy:
                for i in reversed(range(y,cy)):
                    self.setCurrentPos((x,i))
                    skymap.setCurrentPos((x,i))
                    skymap.update()
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
            elif y > cy:
                for i in range(cy,y+1):
                    self.setCurrentPos((x,i))
                    skymap.setCurrentPos((x,i))
                    skymap.update()
                    QtGui.QApplication.processEvents()
                    time.sleep(delay)
        else:
            # This is where live code goes
            # remember self.getCurrentPos() is now in degrees in azalt or radec - NOT pixel coordinates.
            print("Slewing in live mode.")
            (x,y) = pos # target - mouse click position in pixels
            (cx,cy) = self.pos
            print("Target Pos: (" + str(skymap.pixelToDegreeX(x)) + "," + str(skymap.pixelToDegreeY(y)) + ")")
            print("Current Pos: (" + str(skymap.pixelToDegreeX(cx)) + "," + str(skymap.pixelToDegreeY(cy)) + ")")
            # construct a SkyCoord in correct coordinate frame.
            self.drive.goto(skycoord)
            skymap.setCurrentPos() # for updating onscreen position
            skymap.update()
            QtGui.QApplication.processEvents()
            #test again
        print("Finished slewing to " + str(skymap.pixelToDegree(self.getCurrentPos())))
        self.status = Status.READY
        
    def stow(self,pos=(0,90)):
        pass

    def getStatus(self):
        return self.status

    def setStatus(self,status):
        self.status = status

    def sendCommand():
        pass

    def parseCommand():
        pass

    def simulationMode():
        pass
        
    def track():
        pass
