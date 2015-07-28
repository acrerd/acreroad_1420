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
        self.commandButtons = commandButtons(self)
        self.antennaCoordsInfo = antennaCoordsInfo(self)
        self.sourceInfo = sourceInfo(self)
        #self.buttonLayout = buttonLayout(self)
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

class antennaCoordsInfo(QtGui.QWidget):
    def __init__(self,parent):
        super(antennaCoordsInfo,self).__init__(parent)
        self.setGeometry(250,0,200,250)
        gb = QtGui.QGroupBox(self)
        gb.setTitle("Antenna Coordinates")
        gb.setStyleSheet("QGroupBox {border: 2px solid gray; border-radius: 5px; margin-top: 0.5em;} QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}")        
        gb.setFixedSize(200,250)
        layout = QtGui.QVBoxLayout(self)

        self.posLabel = QtGui.QLabel("AzEl: " + "%.2f %.2f" % self.parent().getSRT().getCurrentPos())
        layout.addWidget(self.posLabel)

        self.radecLabel = QtGui.QLabel("Ra Dec: ")
        layout.addWidget(self.radecLabel)
        
        self.galLabel = QtGui.QLabel("Gal: ")
        layout.addWidget(self.galLabel)        

        gb.setLayout(layout)

    def update(self):
        self.posLabel.setText("AzEl: " + "%.2f %.2f" % self.parent().getSRT().getCurrentPos())
        #self.radecLabel.setText()
        #self.galLabel.setText()

class sourceInfo(QtGui.QWidget):
    def __init__(self,parent):
        super(sourceInfo,self).__init__(parent)
        self.setGeometry(0,275,600,100)
        gb = QtGui.QGroupBox(self)
        gb.setTitle("Source Information")
        gb.setStyleSheet("QGroupBox {border: 2px solid gray; border-radius: 5px; margin-top: 0.5em;} QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}")
        gb.setFixedSize(600,100)
        layout = QtGui.QVBoxLayout(self)

        self.nameLabel = QtGui.QLabel("Name: ")
        layout.addWidget(self.nameLabel)

        self.posLabel = QtGui.QLabel("AzEl: ")
        layout.addWidget(self.posLabel)

        self.radecLabel = QtGui.QLabel("Ra Dec: ")
        layout.addWidget(self.radecLabel)
        
        self.galLabel = QtGui.QLabel("Gal: ")
        layout.addWidget(self.galLabel)        

        gb.setLayout(layout)

    def updateEphemLabel(self,src):
        name = src.getName()
        pos = src.getPos()
        #radec = src.getRADEC()
        #gal = src.getGal()
        self.nameLabel.setText("Name: " + name)
        self.posLabel.setText("AzEl: " + "%.2f %.2f" % pos)
        #self.radecLabel.setText()
        #self.galLabel.setText()

class commandButtons(QtGui.QWidget):
    def __init__(self,parent):
        super(commandButtons,self).__init__(parent)
        self.setGeometry(0,0,150,200)
        gb = QtGui.QGroupBox(self)
        gb.setTitle("Control")
        gb.setStyleSheet("QGroupBox {border: 2px solid gray; border-radius: 5px; margin-top: 0.5em;} QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}")
        gb.setFixedSize(150,200)
        layout = QtGui.QVBoxLayout(self)
        buttonWidth = 90
    
        stowButton = QtGui.QPushButton("Stow")
        #stowButton.setMinimumSize(20,50)
        stowButton.setFixedWidth(buttonWidth)
        layout.addWidget(stowButton)
        stowButton.clicked.connect(self.handleStowButton)

        self.slewToggle = SlewToggle.OFF
        slewButton = QtGui.QPushButton("Slew Toggle")
        slewButton.setFixedWidth(buttonWidth)
        slewButton.setCheckable(True)
        layout.addWidget(slewButton)
        slewButton.clicked.connect(self.handleSlewButton)

        trackButton = QtGui.QPushButton("Track")
        trackButton.setFixedWidth(buttonWidth)
        layout.addWidget(trackButton)
        trackButton.clicked.connect(self.handleTrackButton)

        #self.label = QtGui.QLabel("azel: " + str(parent.srt.getCurrentPos()))
        #self.layout.addWidget(self.label,2,2)

        #self.antennaCoordsLabel = QtGui.QLabel("ant coords")
        #self.antennaCoordsLabel.setFrameRect(QtCore.QRect(100,0,100,50))
        #self.antennaCoordsLabel.move(100,0)
        #self.layout.addWidget(self.antennaCoordsLabel,1,2)

        #self.antennaCoordsLabel.show()
        
        #self.setLayout(self.layout)

        gb.setLayout(layout)

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

   
 
   
