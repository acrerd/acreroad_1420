import sys, argparse, ConfigParser, time
from PyQt4 import QtGui, QtCore
from skymap import Skymap
from srt import SRT, Status, Mode
from radiosource import RadioSource,radec,galactic
from astropy.time import Time

class SlewToggle:
    ON = 0
    OFF = 1

class TrackToggle:
    ON = 0
    OFF = 1

class mainWindow(QtGui.QMainWindow):
    """
    Container class for the whole main window.  Container classes for other widgets such as buttons and labels are constructed here.
    """
    def __init__(self, srt, catalogue, parent=None):
        super(mainWindow,self).__init__(parent=parent)
        self.setGeometry(50,50,600,800)
        self.setWindowTitle("SRT Drive Control")
        self.setFocus()
        self.srt = srt
        self.skymap = Skymap(self)
        self.skymap.init(catalogue) # this must be called to get the current position of srt to diplay it on the skymap.

        self.commandButtons = commandButtons(self)
        self.antennaCoordsInfo = antennaCoordsInfo(self)
        self.sourceInfo = sourceInfo(self)
        
        self.infoTimer = QtCore.QTimer(self)
        self.infoTimer.timeout.connect(self.skymap.updateSkymap)
        self.infoTimer.start(100)
        
        self.sourceTimer = QtCore.QTimer(self)
        self.sourceTimer.timeout.connect(self.skymap.fetchRadioSourceCoordinates)
        self.sourceTimer.start(60000)

        
    def updateStatusBar(self,status):
        """
        Update the text of the status bar with the string status.
        """
        self.statusBar().showMessage(str(status))
        
    def getSRT(self):
        return self.srt

    def setMode(self,mode):
        self.mode = mode

    def getMode(self):
        return self.mode

class antennaCoordsInfo(QtGui.QWidget):
    """
    Container class for the widget which displays antenna coordinate information and offsets etc.
    """
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

        self.radecLabel = QtGui.QLabel("Ra Dec: todo ")
        layout.addWidget(self.radecLabel)
        
        self.galLabel = QtGui.QLabel("Gal: todo")
        layout.addWidget(self.galLabel)

        self.utcLabel = QtGui.QLabel("UTC: todo")
        layout.addWidget(self.utcLabel)

        gb.setLayout(layout)

    def updateCoords(self):
        """
        Update is called when the on screen antenna coordinate information should be updated to new values.
        """
        currentPos = self.parent().srt.getCurrentPos()
        self.posLabel.setText("AzEl: " + "%.2f %.2f" % currentPos)
        #self.radecLabel.setText("RaDec: " + "%.2f %.2f" % radec(currentPos))
        #self.galLabel.setText("Gal: " + "%.2f %.2f" % galactic(currentPos))

    def tick(self):
        self.utcLabel.setText("UTC: " + time.strftime("%d %b %y %H:%M:%S",time.gmtime()))

class sourceInfo(QtGui.QWidget):
    """
    A container class for displaying the information about a selected radio source on the skymap.
    """
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
        """
        Whenever it is required to update information about a radio source src.
        """
        name = src.getName()
        pos = src.getPos()
        #radec = src.getRADEC()
        #gal = src.getGal()
        self.nameLabel.setText("Name: " + name)
        self.posLabel.setText("AzEl: " + "%.2f %.2f" % pos)
        #self.radecLabel.setText()
        #self.galLabel.setText()

class commandButtons(QtGui.QWidget):
    """
    Container class for the buttons on the main windows which (usually) instruct the SRT to do something.
    """
    def __init__(self,parent):
        super(commandButtons,self).__init__(parent)
        self.setGeometry(0,0,150,200)
        gb = QtGui.QGroupBox(self)
        gb.setTitle("Control")
        gb.setStyleSheet("QGroupBox {border: 2px solid gray; border-radius: 5px; margin-top: 0.5em;} QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}")
        gb.setFixedSize(150,200)
        layout = QtGui.QVBoxLayout(self)
        buttonWidth = 100
    
        stowButton = QtGui.QPushButton("Stow")
        #stowButton.setMinimumSize(20,50)
        stowButton.setFixedWidth(buttonWidth)
        layout.addWidget(stowButton)
        stowButton.clicked.connect(self.handleStowButton)

        homeButton = QtGui.QPushButton("Home")
        homeButton.setFixedWidth(buttonWidth)
        layout.addWidget(homeButton)
        homeButton.clicked.connect(self.handleHomeButton)

        self.slewToggle = SlewToggle.OFF
        slewButton = QtGui.QPushButton("Slew Toggle")
        slewButton.setFixedWidth(buttonWidth)
        slewButton.setCheckable(True)
        layout.addWidget(slewButton)
        slewButton.clicked.connect(self.handleSlewButton)

        slewToCoordButton = QtGui.QPushButton("Slew to coord")
        slewToCoordButton.setFixedWidth(buttonWidth)
        layout.addWidget(slewToCoordButton)
        slewToCoordButton.clicked.connect(self.handleSlewToCoordButton)
        
        self.trackToggle = TrackToggle.OFF
        trackButton = QtGui.QPushButton("Track Toggle")
        trackButton.setFixedWidth(buttonWidth)
        trackButton.setCheckable(True)
        layout.addWidget(trackButton)
        trackButton.clicked.connect(self.handleTrackButton)

        calibrateButton = QtGui.QPushButton("Calibrate")
        calibrateButton.setFixedWidth(buttonWidth)
        layout.addWidget(calibrateButton)
        calibrateButton.clicked.connect(self.handleCalibrateButton)

        gb.setLayout(layout)

        self.trackSource = RadioSource("ts")
        self.oldTrackSource = RadioSource("ots")
        self.trackTimer = QtCore.QTimer()
        self.trackTimer.timeout.connect(self.handleTrackButton)
        self.trackTimer.setInterval(5000)


    def handleStowButton(self):
        """
        Returns the SRT to its stow position.
        """
        pass

    def handleHomeButton(self):
        """
        """
        self.parent().srt.drive.home()

    def handleSlewButton(self):
        """
        Turns slew capability on/off for selecting/slewing to source on the skymap.
        """
        if self.slewToggle == SlewToggle.ON:
            self.slewToggle = SlewToggle.OFF
            print("Slew toggle OFF")
        elif self.slewToggle == SlewToggle.OFF:
            self.slewToggle = SlewToggle.ON
            print("Slew toggle ON")

    def handleSlewToCoordButton(self):
        """
        An input window will be presented where AzEl coordinates are required to be input.  The SRT will then slew to these coordinates.
        """
        azel, ok = QtGui.QInputDialog.getText(self, 'Input', 
            'Enter Az El:')
        
        if ok:
            # check values
            azs,els = azel.split(" ")
            azf = float(azs)
            elf = float(els)
            valid = False
            if azf < 0 or azf > 360:
                valid = False
            else:
                valid = True

            if elf < 0 or elf > 90:
                valid = False
            else:
                valid = True
            # slew to coords
            if valid:
                #self.parent().srt.slew(self.parent().skymap,(azf,elf))
                currentPos = self.parent().srt.getCurrentPos()
                targetPos = (azf,elf)
                state = self.parent().srt.getStatus()
                if state != Status.SLEWING:
                    if targetPos == currentPos:
                        print("Already at that position.")
                        #self.targetPos = currentPos
                        self.parent().skymap.setTargetPos(currentPos)
                        self.srt.setStatus(Status.READY)
                    else:
                        print("Slewing to " + str(targetPos))
                        self.parent().srt.setStatus(Status.SLEWING)
                        #self.parent().updateStatusBar()
                        self.parent().srt.slew(self,targetPos)
                        #self.currentPos = targetPos
                        self.parent().skymap.setCurrentPos(targetPos)
                        #self.parent().updateStatusBar()
                else:
                    print("Already Slewing.  Please wait until finished.")
                
    def handleTrackButton(self):
        """
        Whenever the track button is pressed, the SRT will begin tracking whatever source is currently seclected.  If it is pressed again and the source hasn't changed, it'll stop tracking that source.
        """
        if self.trackToggle == TrackToggle.OFF:
            self.trackToggle = TrackToggle.ON
            print("Track Toggle ON")
            self.parent().srt.setStatus(Status.TRACKING)
        elif self.trackToggle == TrackToggle.ON:
            self.trackToggle = TrackToggle.OFF
            print("Track Toggle OFF")
            self.parent().srt.setStatus(Status.READY)

    def handleCalibrateButton(self):
        self.parent().srt.calibrate()
        #print("Not implemented yet ...")

    def getSlewToggle(self):
        return self.slewToggle

    def setSlewToggle(self,st):
        self.slewToggle = st

        

def run():
    app = QtGui.QApplication(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('-live',dest='live',action='store_true',
                        help='Starts main in live mode.')
    parser.add_argument('-sim',dest='sim',action='store_true',
                        help='Starts main in simulation mode.')
    args = parser.parse_args()
    if args.live == True and args.sim == False:
        print("Live mode enabled.")
        mode = Mode.LIVE
    elif args.live == False and args.sim == True:
        print("Simulation mode enabled.")
        mode = Mode.SIM

    # parse the _simple_ config file
    config = ConfigParser.SafeConfigParser()
    config.read('settings.cfg')
    device = config.get('arduino','dev')
    catalogue = config.get('catalogue','catfile')

    srt = SRT(mode,device)
    main = mainWindow(srt,catalogue)

    main.show()
    sys.exit(app.exec_())

run()

   
 
   
