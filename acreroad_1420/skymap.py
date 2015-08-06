import random,math,time
from PyQt4 import QtGui, QtCore
from srt import CoordinateSystem,Status,Mode
from radiosource import RadioSource

from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.coordinates import get_sun

class SlewToggle:
    ON = 0
    OFF = 1

class Skymap(QtGui.QWidget):
    """
    The skymap is a widget which plots axes and draws radio sources read in by the catalogue file.
    """
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent=parent)
        x,y,w,h = (0,400,600,300) #probably should be passed as argument in constructor
        self.sceneSize = (x,y,w,h)
        self.scene = QtGui.QGraphicsScene(self)
        self.setGeometry(QtCore.QRect(x,y,w,h))
        self.view = QtGui.QGraphicsView(self.scene, self)
        self.setAutoFillBackground(True)
        p = self.palette() # for white background color
        p.setColor(self.backgroundRole(), QtGui.QColor("white"))
        self.setPalette(p)

        self.coordinateSystem = CoordinateSystem.AZEL # default coordinate system
        self.srt = self.parent().getSRT()

        #self.currentPos = (0,0) # this should always be in azel degrees
        self.targetPos = (0,0) # likewise

        self.radioSources = [] # the list of radio source from radiosources.cat
        self.clickedSource = ""  # name of last clicked source

    def init(self,catalogue):
        """
        Required to set the initial pointing position, initial status and read in the contents of the source catalogue file.
        """
        #self.currentPos = self.srt.getCurrentPos()
        self.readCatalogue(catalogue)
        self.srt.setStatus(Status.READY)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRadioSources(qp)
        self.drawLines(qp)
        self.drawCurrentPosCrosshair(qp)
        self.drawTargetPosCrosshair(qp)
        qp.end()

    def fetchRadioSourceCoordinates(self):
        """
        For each loaded radio source, call its update method to calculate its most current coordinates. TODO: tracking
        """
        for src in self.radioSources:
            src.update()

    def updateSkymap(self):
        targetPos = self.targetPos
        if self.srt.getMode() == Mode.SIM:
            self.setCurrentPos(self.srt.getCurrentPos())
        elif self.srt.getMode() == Mode.LIVE:
            self.setCurrentPos(self.srt.azalt())
            
        if self.srt.getStatus() == Status.CALIBRATING:
            if self.srt.drive.calibrating == False:
                self.srt.setStatus(Status.READY)

        # potential problem here if the telescope never reaches its destination then the status will never be ready and a hard reset is required.
        if self.srt.getStatus() == Status.SLEWING:
            if self.srt.slewSuccess(targetPos) == True:
                self.srt.setStatus(Status.READY)

        self.parent().antennaCoordsInfo.updateCoords()
        self.parent().antennaCoordsInfo.tick()

        if self.clickedSource != "" and type(self.clickedSource) != int:
            self.parent().sourceInfo.updateEphemLabel(self.clickedSource)

        if self.srt.getStatus() == Status.TRACKING:
            source = self.getClickedSource() 
            self.srt.track(self,source)

        self.updateStatusBar()
        self.update()
        QtGui.QApplication.processEvents() # i _think_ this calls self.paintEvent()
        
    def updateStatusBar(self):
        """
        Update the status bar with the current SRT status.
        """
        status = self.srt.getStatus()
        if status == Status.INIT:
            self.parent().updateStatusBar("Status: Initialising")
        elif status == Status.SLEWING:
            self.parent().updateStatusBar("Status: Slewing")
        elif status == Status.PARKED:
            self.parent().updateStatusBar("Status: Parked")
        elif status == Status.CALIBRATING:
            self.parent().updateStatusBar("Status: Calibrating")
        elif status == Status.READY:
            self.parent().updateStatusBar("Status: Ready")
        elif status == Status.TRACKING:
            sourceName = self.getClickedSource().getName()
            self.parent().updateStatusBar("Status: Tracking " + sourceName)
                            
    def setCurrentPos(self,pos):
        self.srt.setCurrentPos(pos)

    def getCurrentPos(self):
        return self.srt.getCurrentPos()

    def setTargetPos(self,pos):
        self.targetPos = pos

    def getTargetPos(self):
        return self.targetPos

    def getCoordinateSystem(self):
        return self.coordinateSystem()

    def setCoordinateSystem(self, coordsys):
        self.coordinateSystem = coordsys

    def getClickedSource(self):
        return self.clickedSource

    def setClickedSource(self,src):
        self.clickedSource = src

    def checkClickedSource(self,clickedPos,r):
        """
        Tests whether a drawn source has been clicked on.
        """
        (x,y) = clickedPos
        for src in self.radioSources:
            (sx,sy) = src.getPos()
            if (abs(x - sx)) < r and (abs(y - sy)) < r:
                name = src.getName()
                return src
            else:
                check = 0
        return check
                

    def mousePressEvent(self, QMouseEvent):
        """
        Event handler for when the cursor is clicked on the skymap area.
        """
        cursor = QtGui.QCursor()
        xf = self.mapFromGlobal(cursor.pos()).x()
        yf = self.mapFromGlobal(cursor.pos()).y()
        (cxf,cyf) = self.getCurrentPos()

        # in simulation mode, the coordinate are rounded to integers.
        if self.srt.getMode() == Mode.SIM:
            x = int(self.pixelToDegreeX(xf))
            y = int(self.pixelToDegreeY(yf))
            currentPos = (int(cxf),int(cyf))
        elif self.srt.getMode() == Mode.LIVE:
            x = self.pixelToDegreeX(xf)
            y = self.pixelToDegreeY(yf)
            currentPos = (cxf,cyf)

        #print(x,y)
        self.clickedSource = self.checkClickedSource((x,y),4)
        #print(self.clickedSource)
        if self.clickedSource != 0:
            #print(self.clickedSource.getName())
            self.parent().sourceInfo.updateEphemLabel(self.clickedSource)
            self.targetPos = self.clickedSource.getPos()
        else:
            self.targetPos = (x,y)

        state = self.srt.getStatus()
        slewToggle = self.parent().commandButtons.getSlewToggle()
        if slewToggle == SlewToggle.ON:
            if state != Status.SLEWING:
                #self.targetPos = targetPos
                if self.targetPos == currentPos:
                    print("Already at that position.")
                    self.targetPos = currentPos
                    self.srt.setStatus(Status.READY)
                else:
                    print("Slewing to " + str(self.targetPos))
                    self.srt.setStatus(Status.SLEWING)
                    self.updateStatusBar()
                    self.srt.slew(self,self.targetPos)
                    #self.currentPos = targetPos
                    self.updateStatusBar()
            else:
                print("Already Slewing.  Please wait until finished.")
        else:
            pass
        self.update()
    
    def drawCurrentPosCrosshair(self,qp):
        """
        Wrapper function for drawing the current aimed direction crosshair.
        """
        color = QtGui.QColor('black')
        self.drawCrosshair(self.getCurrentPos(),color,qp)

    def drawTargetPosCrosshair(self,qp):
        """
        Wrapper function for drawing the chosen target direction crosshair.
        """
        color = QtGui.QColor('green')
        self.drawCrosshair(self.targetPos,color,qp)

    def drawCrosshair(self,pos,color,qp):
        """
        Draws a crosshair (a vertial and horizontal line) at a position pos in degrees.
        """
        x,y = self.degreeToPixel(pos)
        d = 5
        crosshairPen = QtGui.QPen(color,1,QtCore.Qt.SolidLine)
        qp.setPen(crosshairPen)
        qp.drawLine(x-d,y,x+d,y)
        qp.drawLine(x,y-d,x,y+d)
        
    def drawSun(self,qp):
        x,y,w,h = self.sceneSize
        d = 6
        blackSunPen = QtGui.QPen(QtCore.Qt.black,5,QtCore.Qt.SolidLine)
        yellowSunPen = QtGui.QPen(QtCore.Qt.yellow,5,QtCore.Qt.SolidLine)
        qp.setPen(blackSunPen)
        qp.setFont(QtGui.QFont('Decorative', 6))

        # temp astropy for testing

        acre_road = EarthLocation(lat=55.9*u.deg,lon=-4.3*u.deg,height=45*u.m)
        now = Time(time.time(),format='unix')
        altazframe = AltAz(obstime=now, location=acre_road)
        sunaltaz = get_sun(now).transform_to(altazframe)
        alt = float(sunaltaz.alt.degree)
        az = float(sunaltaz.az.degree)

        #obs = ephem.Observer()
        #obs.lon, obs.lat = '-4.3', '55.9'   #glasgow                           
        #obs.date = ephem.now()
        #sun = ephem.Sun()
        #sun.compute(obs)
        #x = float(repr(sun.az))*(180/math.pi)
        #y = float(repr(sun.alt))*(180/math.pi)
        
        qp.drawText(self.degreeToPixelX(az+10),self.degreeToPixelY(alt),"Sun")
        qp.drawEllipse(self.degreeToPixelX(az),self.degreeToPixelY(alt),d,d)
        
        qp.setPen(yellowSunPen)
        qp.drawEllipse(self.degreeToPixelX(az),self.degreeToPixelY(alt),d-2,d-2)

    def drawObject(self,qp,posd,desc):
        """
        Draws an object with description desc on the skymap at posd where posd is azalt position in degrees.
        All drawing must be done in pixel coordinates - use degreeToPixel() functions to convert degrees to pixel coords.
        """
        x,y,w,h = self.sceneSize
        posPixels = self.degreeToPixel(posd)
        x,y = posPixels

        if desc.lower() == "sun":
            d = 6
            blackSunPen = QtGui.QPen(QtCore.Qt.black,5,QtCore.Qt.SolidLine)
            yellowSunPen = QtGui.QPen(QtCore.Qt.yellow,5,QtCore.Qt.SolidLine)
            qp.setPen(blackSunPen)
            qp.setFont(QtGui.QFont('Decorative', 6))
            qp.drawText(x+10,y,"Sun")
            qp.drawEllipse(x,y,d,d)
            qp.setPen(yellowSunPen)
            qp.drawEllipse(x,y,d-2,d-2)
        elif desc.lower() == "moon":
            d = 6
            blackMoonPen = QtGui.QPen(QtCore.Qt.black,5,QtCore.Qt.SolidLine)
            greyMoonPen = QtGui.QPen(QtCore.Qt.gray,5,QtCore.Qt.SolidLine)
            qp.setPen(blackMoonPen)
            qp.setFont(QtGui.QFont('Decorative', 6))
            qp.drawText(x+10,y,"Moon")
            qp.drawEllipse(x,y,d,d)
            qp.setPen(greyMoonPen)
            qp.drawEllipse(x,y,d-2,d-2)
        else:
            d = 4
            objectPen = QtGui.QPen(QtGui.QColor("black"),5,QtCore.Qt.SolidLine)
            qp.setFont(QtGui.QFont('Decorative',6))
            qp.setPen(objectPen)
            qp.drawText(x+10,y,desc)
            qp.drawEllipse(x,y,d,d)

    def drawRadioSources(self,qp):
        """
        Loops through the list of previously constructed radio sources and calls drawObject() to draw them on the skymap.
        """
        for src in self.radioSources:
            name = src.getName()
            pos = src.getPos()
            if src.isVisible() == True:
                #print("%s pos: %s" % (name,pos))
                self.drawObject(qp,pos,name)
            else:
                #print(name + " is not visible currently.")
                pass
        
    def drawPoints(self,qp,n):
        """
        A function for drawing n points randomly distributed on the skymap.
        """
        x,y,w,h = self.sceneSize
        d = 3
        pointsPen = QtGui.QPen(QtCore.Qt.red,6,QtCore.Qt.DashLine)
        qp.setPen(pointsPen)

        for i in range(n):
            x = random.randint(20, w-20)
            y = random.randint(20, h-20)
            qp.drawEllipse(x,y,d,d)
        
    def drawLines(self,qp):
        """
        Draw the axes lines.
        """
        x,y,w,h = self.sceneSize
        
        linesPen = QtGui.QPen(QtCore.Qt.blue,1,QtCore.Qt.DashLine)
        qp.setFont(QtGui.QFont('Decorative', 8))
        qp.setPen(linesPen)

        if self.coordinateSystem == CoordinateSystem.RADEC:
            # Right Ascension
            for i in range(1,24):
                j = (i/24.0)
                qp.drawLine(w*j,1,w*j,h-1)
                qp.drawText(w*j-20,h-20,str(i))

            # Declination
            for i in range(1,10):
                j = 0.1*i
                qp.drawLine(1,h*j,w-1,h*j)
                qp.drawText(w-20,h*j-20,str(i))
        elif self.coordinateSystem == CoordinateSystem.AZEL:
            # Azimuth
            nlines = 18
            for i in range(1,nlines+1):
                j = self.degreeToPixelX(i * (360.0/nlines))
                qp.drawLine(j,1,j,h-1)
                qp.drawText(j-20,h-1,str(i*20))
                
            # Elevation
            nlines = 9
            for i in reversed(range(1,nlines+1)):
                j = self.degreeToPixelY(i * (90.0/nlines))
                qp.drawLine(1,j,w-1,j)
                qp.drawText(w-20,j-5,str(i*10))


    def degreeToPixelX(self,deg):
        (xs,ys,w,h) = self.sceneSize
        return deg * (w/360.0)

    def pixelToDegreeX(self,pixel):
        (xs,ys,w,h) = self.sceneSize
        return pixel * (360.0/w)

    def degreeToPixel(self,deg):
        (xs,ys,w,h) = self.sceneSize
        x,y = deg
        return (x*(w/360.0),(90.0-y)*(h/90.0))

    def degreeToPixelY(self,deg):
        (xs,ys,w,h) = self.sceneSize
        return (90.0-deg) * (h/90.0)

    def pixelToDegreeY(self,pixel):
        (xs,ys,w,h) = self.sceneSize
        return (h-pixel) * (90.0/h)

    def pixelToDegree(self,pixel):
        (xs,ys,w,h) = self.sceneSize
        x,y = pixel
        return (x*(360.0/w),(h-y)*(90.0/h))

    def printSourceInfo(self):
        pass

    def printSources(self):
        for src in self.radioSources:
            print(src.getName())

    def readCatalogue(self,catalogue):
        """
        Reads radio sources from the catalogue file, constructs RadioSource class for each source, gets its coordinates and adds it to the radiosources array.
        """
        fname = str(catalogue)
        fpath = "./"
        f = open(fpath+fname,"r")
        print("Using catalogue file: %s" % f.name)
        print("Loading source information.")

        for line in f:
            name = line.rstrip()
            if name.lower() == "sun":
                src = RadioSource("Sun")
                src.sun()
                self.radioSources.append(src)
                print(line + " - OK.")
            elif name.lower() == "moon":
                src = RadioSource("Moon")
                src.moon()
                self.radioSources.append(src)
                print(line + " - OK.")
            else:
                src = RadioSource(name)
                chk = src.lookupAstropy()
                if chk == True:
                    # found the source online
                    if src.getExists() == True:
                        print(line + " - OK.")
                        self.radioSources.append(src)
                    else:
                        print(line + " - Fail.")
                else:
                    # can't find source online - maybe internet is down - use radec coords if supplied
                    lineList = line.rstrip().split()
                    if len(lineList) > 1:
                        name = lineList[0]
                        ra = lineList[1]
                        dec = lineList[2]
                        print(name,ra,dec)
                        # what if the source name ias a space e.g. cass A
                    else:
                        print(line + " - Fail.")
        f.close()

    
