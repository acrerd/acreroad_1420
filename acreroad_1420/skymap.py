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

        self.coordinateSystem = CoordinateSystem.AZEL
        self.srt = self.parent().getSRT()

        self.currentPos = (0,0) # this should always be in degrees
        self.targetPos = (0,0) # likewise

        self.radioSources = []

    def init(self):
        self.currentPos = self.srt.getCurrentPos()
        self.readCatalogue()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawRadioSources(qp)
        self.drawLines(qp)
        self.drawCurrentPosCrosshair(qp)
        self.drawTargetPosCrosshair(qp)
        qp.end()


    def updateStatusBar(self):
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
                            
    def setCurrentPos(self,pos):
        self.currentPos = pos

    def getCurrentPos(self):
        return self.currentPos

    def getCoordinateSystem(self):
        return self.coordinateSystem()

    def setCoordinateSystem(self, coordsys):
        self.coordinateSystem = coordsys

    def checkClickedSource(self,clickedPos,r):
        """
        Tests whether a drawn source has been clicked on.
        """
        (x,y) = clickedPos
        for src in self.radioSources:
            (sx,sy) = src.getPos()
            if (abs(self.pixelToDegreeX(x) - sx)) < r and (abs(self.pixelToDegreeY(y) - sy)) < r:
                name = src.getName()
                print("You clicked: " + name)
                return src
            else:
                check = 0
        return check
                

    def mousePressEvent(self, QMouseEvent):
        """
        Event handler for when the cursor is clicked on the skymap area.
        """
        cursor = QtGui.QCursor()
        x = self.mapFromGlobal(cursor.pos()).x()
        y = self.mapFromGlobal(cursor.pos()).y()
                
        clickedSource = self.checkClickedSource((x,y),4)
        if clickedSource != 0:
            self.parent().formWidget.updateEphemLabel(clickedSource)

        targetPos = self.pixelToDegree((x,y))
        currentPos = self.currentPos
        state = self.srt.getStatus()
        slewToggle = self.parent().formWidget.getSlewToggle()
        if slewToggle == SlewToggle.ON:
            if state != Status.SLEWING:
                self.targetPos = targetPos
                if targetPos == currentPos:
                    print("Already at that position.")
                    self.targetPos = currentPos
                    self.srt.setStatus(Status.READY)
                else:
                    print("Slewing to " + str(targetPos))
                    self.srt.setStatus(Status.SLEWING)
                    self.updateStatusBar()
                    self.srt.slew(self,targetPos)
                    self.currentPos = targetPos
                    self.updateStatusBar()
            else:
                print("Already Slewing.  Please wait until finished.")
        else:
            pass
        self.update()
    
    def drawCurrentPosCrosshair(self,qp):
        color = QtGui.QColor('black')
        self.drawCrosshair(self.currentPos,color,qp)

    def drawTargetPosCrosshair(self,qp):
        color = QtGui.QColor('green')
        self.drawCrosshair(self.targetPos,color,qp)

    def drawCrosshair(self,pos,color,qp):
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
        for src in self.radioSources:
            name = src.getName()
            pos = src.getPos()
            if src.isVisible() == True:
                #print("Source pos: " + str(pos))
                self.drawObject(qp,pos,name)
            else:
                #print(name + " is not visible currently.")
                pass
        

    def drawPoints(self,qp,n):
        x,y,w,h = self.sceneSize
        d = 3
        pointsPen = QtGui.QPen(QtCore.Qt.red,6,QtCore.Qt.DashLine)
        qp.setPen(pointsPen)

        for i in range(n):
            x = random.randint(20, w-20)
            y = random.randint(20, h-20)
            qp.drawEllipse(x,y,d,d)
        
    def drawLines(self,qp):
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

    def readCatalogue(self):
        fname = "radiosources.cat"
        fpath = "./"
        f = open(fpath+fname,"r")
        print("Using catalogue file: %s" % f.name)
        print("Loading source information.")

        # sun and moon from pyephem - handle separetly
        #src = RadioSource("Sun")
        #src.sun()
        #self.radioSources.append(src)
        #print(src.getName() + "\n" + " - OK.")
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
                src.lookupAstropy()
                if src.getExists() == True:
                    print(line + " - OK.")
                    self.radioSources.append(src)
                else:
                    print(line + " - Fail.")
        f.close()

    
