import sys, argparse
from PyQt4 import QtGui, QtCore
from skymap import Skymap
from srt import SRT, Mode

class SlewToggle:
    ON = 0
    OFF = 1

class mainWindow(QtGui.QMainWindow):
    def __init__(self, srt, parent=None):
        super(mainWindow,self).__init__(parent=parent)
        self.setGeometry(50,50,600,800)
        self.setWindowTitle("SRT Drive Control")
        self.setFocus()
        self.srt = srt
        self.skymap = Skymap(self)
        #self.skymap.setCurrentPos(self.srt.getCurrentPos())
        self.skymap.init()
        self.updateStatusBar("This is the status bar.")
        self.formWidget = formWidget(self)
        #self.setCentralWidget(self.formWidget)
        #self.mode = Mode.SIM # default
        
    def updateStatusBar(self,status):
        self.statusBar().showMessage(str(status))
        
    def getSRT(self):
        return self.srt

    def setMode(self,mode):
        self.mode = mode

    def getMode(self):
        return self.mode

class buttonLayout(QtGui.QWidget):
    def __init__(self,parent):
        super(buttonWidget,self).__init__(parent)
        self.setGeometry(300,0,300,300)
        gb = QtGui.QGroupBox()

class formWidget(QtGui.QWidget):
    def __init__(self,parent):
        super(formWidget,self).__init__(parent)
        self.setGeometry(0,0,300,300)
        #self.layout = QtGui.QVBoxLayout(self)
        self.layout = QtGui.QGridLayout(self)
        self.layout.setHorizontalSpacing(200)
        buttonWidth = 90
    
        self.stowButton = QtGui.QPushButton("Stow")
        #self.stowButton.setMinimumSize(20,50)
        self.stowButton.setFixedWidth(buttonWidth)
        self.layout.addWidget(self.stowButton,1,1)
        self.stowButton.clicked.connect(self.handleStowButton)

        self.slewToggle = SlewToggle.OFF
        self.slewButton = QtGui.QPushButton("Slew Toggle")
        self.slewButton.setFixedWidth(buttonWidth)
        self.slewButton.setCheckable(True)
        self.layout.addWidget(self.slewButton,2,1)
        self.slewButton.clicked.connect(self.handleSlewButton)

        self.trackButton = QtGui.QPushButton("Track")
        self.trackButton.setFixedWidth(buttonWidth)
        self.layout.addWidget(self.trackButton,3,1)
        self.trackButton.clicked.connect(self.handleTrackButton)

        self.label = QtGui.QLabel("azel: " + str(parent.srt.getCurrentPos()))
        self.layout.addWidget(self.label,2,2)

        self.antennaCoordsLabel = QtGui.QLabel("ant coords")
        #self.antennaCoordsLabel.setFrameRect(QtCore.QRect(100,0,100,50))
        #self.antennaCoordsLabel.move(100,0)
        self.layout.addWidget(self.antennaCoordsLabel,1,2)

        #self.antennaCoordsLabel.show()
        
        self.setLayout(self.layout)

    def handleStowButton(self):
        pass

    def handleSlewButton(self):
        if self.slewToggle == SlewToggle.ON:
            self.slewToggle = SlewToggle.OFF
            print("Slew toggle OFF")
        elif self.slewToggle == SlewToggle.OFF:
            self.slewToggle = SlewToggle.ON
            print("Slew toggle ON")

    def handleTrackButton(self):
        pass
        
    def updateEphemLabel(self,src):
        name = src.getName()
        pos = src.getPos()
        self.label.setText(name + " " + "%.2f %.2f" % pos)

    def getSlewToggle(self):
        return self.slewToggle

    def setSlewToggle(self,st):
        self.slewToggle = st

        

def run():
    app = QtGui.QApplication(sys.argv)
    #srt = SRT()
    #main = mainWindow(srt)

    parser = argparse.ArgumentParser()
    parser.add_argument('-live',dest='live',action='store_true',
                        help='Starts main in live mode.')
    parser.add_argument('-sim',dest='sim',action='store_true',
                        help='Starts main in simulation mode.')
    args = parser.parse_args()
    #print(args.live,args.sim)
    if args.live == True and args.sim == False:
        print("Live mode enabled.")
        #main.setMode(Mode.LIVE)
        mode = Mode.LIVE
    elif args.live == False and args.sim == True:
        print("Simulation mode enabled.")
        #main.setMode(Mode.SIM)
        mode = Mode.SIM

    srt = SRT(mode)
    main = mainWindow(srt)
    
    
    #skymap_size = (100,0,100,100)
    #pos = (80,100)
    #srt = SRT()
    #skymap = Skymap(main)
    #skymap.setCurrentPos(pos)
    #skymap.init()
    main.show()
    sys.exit(app.exec_())

run()

   
 
   
