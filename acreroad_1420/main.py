#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry for SRT drive control.
Author: Ronnie Frith
Contact: frith.ronnie@gmail.com
"""

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
        screen = QtGui.QDesktopWidget().screenGeometry()        
        #self.showMaximized()
        self.setGeometry(50,50,700,400)
        self.setWindowTitle("SRT Drive Control")
        self.setFocus()
        self.srt = srt
        self.skymap = Skymap(self, time=srt.drive.current_time, location=srt.drive.location)
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
        screen = QtGui.QDesktopWidget().screenGeometry()         
        self.setGeometry(0,-8,screen.width(),38)
        gb = QtGui.QGroupBox(self)
        #gb.setTitle("Antenna Coordinates")
        gb.setStyleSheet("QGroupBox {background: black; color: #ffffff; margin-top: 0.5em; margin-bottom: 0.5em;}")        
        gb.setFixedSize(screen.width(),200)
        layout = QtGui.QHBoxLayout(self)
        #self.setLayout(layout)
        position = self.parent().getSRT().skycoord()
        
        self.posLabel = QtGui.QLabel(" <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>Az</span>: " + "%.2f %.2f" % self.parent().getSRT().getCurrentPos())
        layout.addWidget(self.posLabel)

        self.radecLabel = QtGui.QLabel("Ra Dec: {0.ra:.2f} {0.dec:.2f}".format( position.transform_to('icrs')  ))
        layout.addWidget(self.radecLabel)
        
        self.galLabel = QtGui.QLabel("Gal: {0.l:.2f} {0.b:.2f}".format(position.transform_to('galactic')))
        layout.addWidget(self.galLabel)

        self.utcLabel = QtGui.QLabel("UTC: todo")
        layout.addWidget(self.utcLabel)

        #self.sidLabel = QtGui.QLabel("Sidereal: todo")
        #layout.addWidget(self.sidLabel)

        vbox = QtGui.QVBoxLayout()
        #vbox.addStretch(1)
        vbox.addLayout(layout)

    def updateCoords(self):
        """
        Update is called when the on screen antenna coordinate information should be updated to new values.
        """
        currentPos = self.parent().getSRT().skycoord()
        self.posLabel.setText(" <span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0.az.value:.2f}</span>  <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>az</span> <span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0.alt.value:.2f}</span>  <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>alt</span>".format(currentPos))
        self.radecLabel.setText("<span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0.ra.value:.2f}<span>  <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>ra</span> <span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0.dec.value:.2f}</span> <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>dec</span>" .format(currentPos.transform_to('icrs')))
        self.galLabel.setText("<span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0.l.value:.2f}<span>  <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>lat</span> <span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0.b.value:.2f}</span>  <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>lon</span>".format(currentPos.transform_to('galactic')))

    def tick(self):
        self.utcLabel.setText(" <span style='font-family:mono,fixed; background: black; font-size:16pt; font-weight:600; color:#ffffff;'>{0}</span> <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>UTC</span>".format(time.strftime("%H:%M:%S",time.gmtime())))
        #self.sidLabel.setText("Sidereal: {0.sidereal_time()}".format(self.parent().getSRT().drive.current_time_local))

class sourceInfo(QtGui.QWidget):
    """
    A container class for displaying the information about a selected radio source on the skymap.
    """
    def __init__(self,parent):
        super(sourceInfo,self).__init__(parent)
        screen = QtGui.QDesktopWidget().screenGeometry()         
        self.setGeometry(screen.width()-290,275,260,200)
        gb = QtGui.QGroupBox(self)
        #gb.setTitle("Source Information")
        gb.setStyleSheet("QGroupBox {background: #dddddd; margin: 0.5em; } *[class=objectName]{font-size: 24pt;}")
        gb.setFixedSize(600,100)
        layout = QtGui.QVBoxLayout(self)

        self.nameLabel = QtGui.QLabel("")
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
        skycoord = src.skycoord
        #radec = src.getRADEC()
        #gal = src.getGal()
        
        self.nameLabel.setText("<span style='font-weight: 600; color: blue;'>{}</span>".format(name))
        self.posLabel.setText("AzEl: {0.az.value:.2f} az {0.alt.value:.2f} el".format(skycoord))
        self.radecLabel.setText("{0.ra.value:.2f} {0.dec.value:.2f}".format(skycoord.transform_to('icrs')))
        galco = skycoord.transform_to('galactic')
        self.galLabel.setText(u"{0:.0f}°{1[2]:.0f}'{1[3]:.2f}\" l   {2:.0f}°{3[2]:.0f}'{3[3]:.2f}\" b".format(galco.l.signed_dms[0]*galco.l.signed_dms[1], \
                                                                                                                                galco.l.signed_dms, \
                                                                                                                                galco.b.signed_dms[0]*galco.b.signed_dms[1],\
                                                                                                                                galco.b.signed_dms))

class commandButtons(QtGui.QWidget):
    """
    Container class for the buttons on the main windows which (usually) instruct the SRT to do something.
    """
    def __init__(self,parent):
        super(commandButtons,self).__init__(parent)
        #self.setGeometry(0,0,150,200)
        screen = QtGui.QDesktopWidget().screenGeometry()         
        self.setGeometry(0,20,screen.width(),60)
        gb = QtGui.QGroupBox(self)
        #gb.setStyleSheet("QGroupBox {background: black; color: #ffffff; margin-top: 0.5em; margin-bottom: 0.5em;}")        
        gb.setFixedSize(screen.width(),200)
        layout = QtGui.QHBoxLayout(self)
        #gb = QtGui.QGroupBox(self)
        #gb.setTitle("Control")
        #gb.setStyleSheet("QGroupBox {border: 2px solid gray; border-radius: 5px; margin-top: 0.5em;} QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}")
        #gb.setFixedSize(150,200)
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

        layout = QtGui.QVBoxLayout(self)
        gb.setLayout(layout)

        self.trackSource = RadioSource("ts")
        self.oldTrackSource = RadioSource("ots")
        self.trackTimer = QtCore.QTimer()
        self.trackTimer.timeout.connect(self.handleTrackButton)
        self.trackTimer.setInterval(5000)

        self.offset = (0,0) #azel

    def setOffset(self,offset):
        self.offset = offset

    def getOffset(self):
        return self.offset

    def handleStowButton(self):
        """
        Returns the SRT to its stow position.
        """
        self.parent().skymap.setTargetPos((0,90))
        self.parent().srt.stow()

    def handleHomeButton(self):
        """
        Returns the SRT to its home position.
        """
        #homeOffset = self.getOffset().split()
        #self.parent().skymap.setTargetPos((float(homeOffset[0]),float(homeOffset[1])))
        self.parent().skymap.setTargetPos((self.parent().srt.drive.az_home,self.parent().srt.drive.el_home))
        self.parent().srt.home()

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
                        self.parent().skymap.setTargetPos(targetPos)
                        self.parent().srt.slew(targetPos)
                        #self.parent().skymap.setCurrentPos(targetPos)
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

    def getSlewToggle(self):
        return self.slewToggle

    def setSlewToggle(self,st):
        self.slewToggle = st

def readConfigFile():
    pass

def writeConfigFile():
    pass
        

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
    calibrationSpeeds = config.get('calibration','speeds')
    homeOffset = config.get('offsets','home')
    #calibrationSpeeds = (cs.split()[0],cs.split()[1])
    #print(calibrationSpeeds.split()[0],calibrationSpeeds.split()[1])

    srt = SRT(mode,device,calibrationSpeeds)
    main = mainWindow(srt,catalogue)
    main.commandButtons.setOffset(homeOffset) # this is not the way to do this.

    main.show()
    sys.exit(app.exec_())

run()

   
 
   
