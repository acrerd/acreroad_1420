"""
Skymap draws the axes, radio source positions, current and target position crosshairs.
Author: Ronnie Frith
Contact: frith.ronnie@gmail.com
"""

import random,math,time
from PyQt4 import QtGui, QtCore
from srt import CoordinateSystem,Status,Mode
from radiosource import RadioSource, GalacticPlane

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
    def __init__(self,parent=None, time=None, location=None):
        QtGui.QWidget.__init__(self,parent=parent)
        screen = QtGui.QDesktopWidget().screenGeometry()         
        x,y,w,h = (0,70,500,330) #probably should be passed as argument in constructor
        self.sceneSize = (x,y,w,h)
        self.scene = QtGui.QGraphicsScene(self)
        self.setGeometry(QtCore.QRect(x,y,w,h))
        self.view = QtGui.QGraphicsView(self.scene, self)
        self.setAutoFillBackground(True)
        p = self.palette() # for white background color
        p.setColor(self.backgroundRole(), QtGui.QColor("white"))
        self.setPalette(p)

        self.time = time
        self.location = location
        
        self.coordinateSystem = CoordinateSystem.AZEL # default coordinate system
        self.drive = self.parent().drive

        #self.currentPos = (0,0) # this should always be in azel degrees
        self.targetPos = self.drive.current_position

        self.radioSources = [] # the list of radio source from radiosources.cat
        self.galaxy = GalacticPlane(time = self.time, location=self.location)
        self.clickedSource = ""  # name of last clicked source

    def init_cat(self,catalogue):
        """
        Required to set the initial pointing position, initial status and read in the contents of the source catalogue file.
        """
        self.readCatalogue(catalogue)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRadioSources(qp)
        self.drawLines(qp)
        self.drawCurrentPosCrosshair(qp)
        self.drawTargetPosCrosshair(qp)
        self.drawGalaxy(qp)
        qp.end()

    def fetchRadioSourceCoordinates(self):
        """
        For each loaded radio source, call its update method to calculate its most current coordinates. TODO: tracking
        """
        for src in self.radioSources:
            src.update()
        self.galaxy.update()

    def updateSkymap(self):
        """
        """
        targetPos = self.targetPos

        self.parent().antennaCoordsInfo.updateCoords()
        self.parent().antennaCoordsInfo.tick()

        if self.clickedSource != "" and type(self.clickedSource) != int:
            self.parent().sourceInfo.updateEphemLabel(self.clickedSource)


        #self.updateStatusBar()
        self.update()
        QtGui.QApplication.processEvents() # i _think_ this calls self.paintEvent()
        
    def updateStatusBar(self):
        """
        Update the status bar with the current SRT status.
        """
        if not self.drive.ready:
            self.parent().updateStatusBar("Status: Initialising")
        elif self.drive.slewing:
            self.parent().updateStatusBar("Status: Slewing")
        # elif self.drive.
        #     self.parent().updateStatusBar("Status: Parked")
        elif self.drive.calibrating:
            self.parent().updateStatusBar("Status: Calibrating")
        elif self.drive.ready:
            self.parent().updateStatusBar("Status: Ready")
        elif self.drive.tracking:
            self.parent().updateStatusBar("Status: Tracking")

    def getCurrentPos(self):
        skycoord =  self.drive.current_position
        return (skycoord.az.value, skycoord.alt.value)

    def setTargetPos(self,pos):
        if isinstance(pos, tuple):
            pos = SkyCoord(AltAz(az=pos[0]*u.deg, alt=pos[1]*u.deg,
                                 obstime=self.drive.current_time,
                                 location=self.drive.location))

        self.updateSkymap()
        return pos


    def getCoordinateSystem(self):
        return self.coordinateSystem()

    def setCoordinateSystem(self, coordsys):
        self.coordinateSystem = coordsys

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
        if self.drive.simulate:
            x, y = self.pixelToDegree((xf, yf))
            currentPos = (int(cxf),int(cyf))
        else:
            x, y = self.pixelToDegree((xf, yf))
            currentPos = (cxf,cyf)

        slewToggle = self.parent().commandButtons.getSlewToggle()

        

        self.clickedSource = self.checkClickedSource((x,y),4)
        if self.clickedSource != 0:
            self.parent().sourceInfo.updateEphemLabel(self.clickedSource)
            if slewToggle == SlewToggle.ON: 
                self.setTargetPos(self.clickedSource.getPos())
        else:
            if slewToggle == SlewToggle.ON and not self.drive.slewing:
                self.setTargetPos((x,y))

        #if slewToggle == SlewToggle.ON:

        if self.targetPos == currentPos:
            print("Already at that position.")
            self.setTargetPos(currentPos)
        else:
            print("Slewing to " + str(self.targetPos))
            self.updateStatusBar()
            self.drive.goto(self.targetPos)
            self.updateStatusBar()


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
        crosshairPen = QtGui.QPen(color,3,QtCore.Qt.SolidLine)
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

        labelPos = self.degreeToPixel(az+10, alt)
        ellipsePos = self.degreeToPixel(az, alt)
        qp.drawText(labelPos[0], labelPos[1],"Sun")
        qp.drawEllipse(ellipsePos[0], ellipsePos[1],d,d)
        
        qp.setPen(yellowSunPen)
        qp.drawEllipse(ellipsePos[0], ellipsePos[1],d-2,d-2)

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
        
    def drawLines(self,qp):
        """
        Draw the axes lines.
        """
        x,y,w,h = self.sceneSize
        
        linesPen = QtGui.QPen(QtGui.QColor(0,0,10, 30),1)
        qp.setFont(QtGui.QFont('Decorative', 8))
        qp.setPen(linesPen)
        qp.setRenderHint(qp.Antialiasing)

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
                j = self.degreeToPixel((i * (360.0/nlines), 0))[0]
                qp.drawLine(j,1,j,h-1)
                qp.drawText(j-20,h-1,str(i*20))
                
            # Elevation
            nlines = 9
            for i in reversed(range(1,nlines+1)):
                j = self.degreeToPixel((0, i * (90.0/nlines)))[1]
                qp.drawLine(1,j,w-1,j)
                qp.drawText(w-20,j-10,str(i*10))

    def drawGalaxy(self, qp):
        """
        Draw in the galactic plane.
        """
        linesPen = QtGui.QPen(QtGui.QColor(255, 100, 0, 255),3)
        qp.setFont(QtGui.QFont('Decorative', 8))
        qp.setPen(linesPen)

        c = self.galaxy.points
        pix = []
        for point in c:
            pix.append(self.degreeToPixel(point))
            
        for i in xrange(len(pix)-1):
            #j = i + 1
            #if pix[i][0]<pix[j][0]: continue # avoids drawing a line across the screen when the plane crosses the wrap-over.
            qp.drawEllipse(pix[i][0], pix[i][1],1,1) #, pix[j][0], pix[j][1])


    def degreeToPixel(self, pos):
        """
        Convert a location in degrees to a pixel location on the skymap.
        
        Parameters
        ----------
        pos : tuple or `SkyCoord`
           The azimuth and altitude in degrees, as a tuple, or
           the skycoordinate object.
        """       
        if isinstance(pos, SkyCoord):
            pos = (pos.az.value, pos.alt.value)
            
        (xs, ys, w, h) = self.sceneSize
        x, y = pos
        return (x*(w/360.0), (90.0-y)*(h/90.0))


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
        fpath = ""
        f = open(fpath+fname,"r")
        print("Using catalogue file: %s" % f.name)
        print("Loading source information.")

        for line in f:
            name = line.rstrip()
            if name.lower() == "sun":
                src = RadioSource("Sun")
                src.sun()
                self.radioSources.append(src)
            elif name.lower() == "moon":
                src = RadioSource("Moon")
                src.moon()
                self.radioSources.append(src)
            else:
                src = RadioSource(name)
                chk = src.lookupAstropy()
                if chk == True:
                    # found the source online
                    if src.getExists() == True:
                        self.radioSources.append(src)
                    else:
                        pass
                else:
                    # can't find source online - maybe internet is down - use radec coords if supplied
                    lineList = line.rstrip().split()
                    if len(lineList) > 1:
                        name = lineList[0]
                        ra = lineList[1]
                        dec = lineList[2]
                        # what if the source name ias a space e.g. cass A
                    else:
                        pass
        f.close()

    
