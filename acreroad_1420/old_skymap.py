import random
from PyQt4 import QtGui, QtCore
from srt import CoordinateSystem,Status,Mode

class Skymap(QtGui.QGraphicsView):
    def __init__(self,parent=None):
        QtGui.QGraphicsView.__init__(self,parent=parent)
        #super(self.__class__,self).__init__()
	#super(Skymap,self).__init__(self)
        self.setHorizontalScrollBarPolicy(1)
        self.setVerticalScrollBarPolicy(1)
        x,y,w,h = (0,400,600,300) #probably should be passed as argument in constructor
        self.sceneSize = (x,y,w,h)
        self.scene = QtGui.QGraphicsScene(self)
        self.setGeometry(QtCore.QRect(x,y,w,h))        

        self.coordinateSystem = CoordinateSystem.RADEC

        #self.axisLines = QtGui.QGraphicsItemGroup()
        #self.Points = QtGui.QGraphicsItemGroup()
        self.targetCrosshair = QtGui.QGraphicsItemGroup()
        self.scene.addItem(self.targetCrosshair)
        self.currentPosCrosshair = QtGui.QGraphicsItemGroup()
        self.scene.addItem(self.currentPosCrosshair)
        
        self.currentPosition = (0,0)
        self.targetPosition = (0,0)

    def init(self):
        self.drawCurrentPosCrosshair(self.currentPosition,self.currentPosCrosshair)
        self.drawPoints(50)
        self.drawLines()
        self.setScene(self.scene)
                
    def setCurrentPos(self,pos):
        self.currentPosition = pos

    def getCurrentPos(self):
        return self.currentPosition

    def getCoordinateSystem(self):
        return self.coordinateSystem()

    def setCoordinateSystem(self, coordsys):
        self.coordinateSystem = coordsys

    def mousePressEvent(self, QMouseEvent):
        cursor = QtGui.QCursor()
        x = self.mapFromGlobal(cursor.pos()).x()
        y = self.mapFromGlobal(cursor.pos()).y()
        targetPos = (x,y)
        currentPos = self.parent().getSRT().getCurrentPos()
        state = self.parent().getSRT().getStatus()
        if state != Status.SLEWING:
            if targetPos == currentPos:
                print("Already at that position.")
                self.targetPosition = currentPos
            else:
                print("Slewing to " + str(targetPos))

                print(self.currentPosCrosshair.pos().x())
                self.parent().getSRT().slew(self,targetPos)
                print(self.currentPosCrosshair.pos().x())
                #self.slewAnimation(targetPos)
                self.targetPosition = targetPos
        else:
            print("Already Slewing.  Please wait until finished.")
        self.update()

    
    def slewAnimation(self, targetPos):
        """Polls current position of SRT and draws crosshair on screen."""
        currentPos = self.parent().getSRT().getCurrentPos()
        #while the current pos does not equal the requested pos
        # delete old cursor and draw one at new position
        cx,cy = currentPos
        x,y = targetPos
        #self.removeCrosshair(self.currentPosCrosshair)
        #self.drawCurrentPosCrosshair(currentPos,self.currentPosCrosshair)
        #print(currentPos)
        #time.sleep(0.2)
        self.moveCrosshair(self.currentPosCrosshair,targetPos)
        #self.tl.end()
        #while ((cx != x) and (cy != y)):
        #    self.drawCurrentPosCrosshair(currentPos)
        #    currentPos = self.parent().getSRT().getCurrentPos()
        #    cx,cy = currentPos

    def moveCrosshair(self,crosshair,pos):
        (x,y) = pos
        #p = self.mapFromGlobal(QtCore.QPoint(x,y))
        #print(x,y)
        crosshair.setPos(x,y)
        #self.update()

    def drawCurrentPosCrosshair(self,pos,crosshair):
        color = QtGui.QColor('black')
        self.drawCrosshair(pos,color,crosshair)

    def drawTargetPosCrosshair(self,pos):
        color = QtGui.QColor('green')
        self.drawCrosshair(pos,color)

    def removeCrosshair(self,crosshair):
        self.scene.destroyItemGroup(crosshair)

    def drawCrosshair(self,pos,color,crosshair):
        x,y = pos
        d = 5
        pen = QtGui.QPen(color)
        #crosshair = QtGui.QGraphicsItemGroup()
        l1 = QtGui.QGraphicsLineItem(x-d,y,x+d,y)
        l1.setPen(pen)
        l2 = QtGui.QGraphicsLineItem(x,y-d,x,y+d)
        l2.setPen(pen)
        crosshair.addToGroup(l1)
        crosshair.addToGroup(l2)
        #self.scene.addItem(crosshair)
  
    def getItems(self):
        return self.scene.items()

    def drawPoints(self,n):
        clr   = QtGui.QColor('red')
        brush = QtGui.QBrush(clr)
        pen   = QtGui.QPen(clr)
        x,y,w,h = self.sceneSize
        points = QtGui.QGraphicsItemGroup()

        for i in range(n):
            x = random.randint(20, w-20)
            y = random.randint(20, h-20)
            point = QtGui.QGraphicsEllipseItem(x,y,5,5)
            point.setPen(pen)
            point.setBrush(brush)
            points.addToGroup(point)
            
        self.scene.addItem(points)

    def drawLines(self):
        pen = QtGui.QPen(QtGui.QColor('blue'))
        font = QtGui.QFont('Decorative', 10)
        x,y,w,h = self.sceneSize
        lines = QtGui.QGraphicsItemGroup()
        text = QtGui.QGraphicsItemGroup()

        if self.coordinateSystem == CoordinateSystem.RADEC:
            # Right Ascension
            for i in range(1,24):
                j = (i/24.0)
                line = QtGui.QGraphicsLineItem(w*j, 1, w*j, h-1)
                line.setPen(pen)
                lines.addToGroup(line)
                t = QtGui.QGraphicsTextItem(str(i))
                t.setFont(font)
                t.setPos(w*j-20,h-20)
                text.addToGroup(t)
            
            # Declination
            for i in range(1,10):
                j = 0.1*i
            
                line = QtGui.QGraphicsLineItem(1, h*j, w-1, h*j)
                line.setPen(pen)
                lines.addToGroup(line)
    
                t = QtGui.QGraphicsTextItem(str(i))
                t.setFont(font)
                t.setPos(w-20,h*j-20)
                text.addToGroup(t)
    
            self.scene.addItem(lines)
            self.scene.addItem(text)



    
