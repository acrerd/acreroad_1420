#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Main entry for SRT drive control.
Author: Ronnie Frith
Contact: frith.ronnie@gmail.com
"""

from . import CONFIGURATION as config
from . import CATALOGUE
from .drive import Drive

#from acreroad_1420 import CONFIGURATION as config
import numpy as np
import sys, argparse, time
from PyQt4 import QtGui, QtCore
from skymap import Skymap
from srt import SRT, Status, Mode
from radiosource import RadioSource,radec,galactic
from astropy.time import Time
from formlayout import fedit
import astropy
import astropy.units as u
from astropy.coordinates import SkyCoord, ICRS, EarthLocation, AltAz

from os.path import expanduser, isfile, join
import os.path


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
    OFFSET_CHANGE = 1.1

    cursorkeys = [QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]
    
    def __init__(self, drive, catalogue, parent=None):
        super(mainWindow,self).__init__(parent=parent)
        screen = QtGui.QDesktopWidget().screenGeometry()        
        #self.showMaximized()
        self.setGeometry(50,50,700,450)
        self.setWindowTitle("SRT Drive Control")
        self.setFocus()

        self.drive = drive
        
        self.skymap = Skymap(self, time=self.drive.current_time, location=self.drive.location)
        self.skymap.init_cat(CATALOGUE)
        

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
        self.setGeometry(0,-8,700,38)
        gb = QtGui.QGroupBox(self)
        #gb.setTitle("Antenna Coordinates")
        gb.setStyleSheet("QGroupBox {background: black; color: #ffffff; margin-top: 0.5em; margin-bottom: 0.5em; font-size: 10pt;}")        
        gb.setFixedSize(screen.width(),200)
        layout = QtGui.QHBoxLayout(self)
        #self.setLayout(layout)
        position = self.parent().drive.current_position
        
        self.posLabel = QtGui.QLabel(
            """<span style='font-family:mono,fixed; 
            background: black; font-size:8pt; font-weight:600; 
            color:#dddddd;'>
            AltAz</span>: {0.alt:.2f} {0.az:.2f} """.format(self.parent().drive.current_position))
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
        currentPos = self.parent().drive.skycoord()
        self.posLabel.setText("<span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0.az.value:.2f}</span> <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd; left: -5px;'>az</span> <span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0.alt.value:.2f}</span>  <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>alt</span>".format(currentPos))
        self.radecLabel.setText("<span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0.ra.value:.2f}<span><span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>ra</span> <span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0.dec.value:.2f}</span><span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>dec</span>" .format(currentPos.transform_to('icrs')))
        self.galLabel.setText("<span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0.l.value:.2f}<span><span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>lon</span> <span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0.b.value:.2f}</span><span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>lat</span>".format(currentPos.transform_to('galactic')))

    def tick(self):
        self.utcLabel.setText(" <span style='font-family:mono,fixed; background: black; font-size:12pt; font-weight:600; color:#ffffff;'>{0}</span> <span style='font-family:mono,fixed; background: black; font-size:8pt; font-weight:600; color:#dddddd;'>UTC</span>".format(time.strftime("%H:%M:%S",time.gmtime())))
        #self.sidLabel.setText("Sidereal: {0.sidereal_time()}".format(self.parent().getSRT().drive.current_time_local))

class sourceInfo(QtGui.QWidget):
    """
    A container class for displaying the information about a selected radio source on the skymap.
    """
    def __init__(self,parent):
        super(sourceInfo,self).__init__(parent)
        screen = QtGui.QDesktopWidget().screenGeometry()         
        self.setGeometry(700-190,105,180,100)
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
        self.setGeometry(0,20,700,60)
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
        #current_az = self.srt.getCurrentPos()[0]
        self.parent().skymap.setTargetPos((0,90))
        self.parent().drive.stow()
        self.parent().setFocus()

    def handleHomeButton(self):
        """
        Returns the SRT to its home position.
        """
        #homeOffset = self.getOffset().split()
        #self.parent().skymap.setTargetPos((float(homeOffset[0]),float(homeOffset[1])))
        self.parent().skymap.setTargetPos((self.parent().drive.az_home,self.parent().drive.el_home))
        self.parent().drive.home()
        self.parent().setFocus()

    def handleSlewButton(self):
        """
        Turns slew capability on/off for selecting/slewing to source on the skymap.
        """
        if self.slewToggle == SlewToggle.ON:
            self.slewToggle = SlewToggle.OFF
            #print("Slew toggle OFF")
        elif self.slewToggle == SlewToggle.OFF:
            self.slewToggle = SlewToggle.ON
            #print("Slew toggle ON")
        self.parent().setFocus()

    def _parseInput(self, data):
        print data
        eq, ho, ga = data[0], data[1], data[2]
        if  (not eq[0] == '') and (not eq[1] == ''):
            frame = 'ICRS'
            # "Parsing an RA and Dec"
            eq[0], eq[1] = np.float(eq[0]), np.float(eq[1])
            c = SkyCoord(ra=eq[0]*u.deg, dec=eq[1]*u.deg, frame='icrs')
            
        elif (not ho[0]=='') and (not ho[1]==''):
            # Parsing a horizontal coordinate
            ho[0], ho[1] = np.float(ho[0]), np.float(ho[1])
            c = SkyCoord(AltAz(ho[0]*u.deg, ho[1]*u.deg, obstime=self.parent().drive.current_time, location=self.parent().drive.location))
            
        elif (not ga[0]=='') and (not ga[1]==''):
            # Parsing a galactic coordinate
            ga[0], ga[1] = np.float(ga[0]), np.float(ga[1])
            c = SkyCoord(l=ga[0]*u.deg, b=ga[1]*u.deg, frame='galactic')

        else:
            # No valid coordinates were passed
            return None
        return c

    def handleSlewToCoordButton(self):
        """
        An input window will be presented where AzEl coordinates are required to be input.  The SRT will then slew to these coordinates.
        """
        # azel, ok = QtGui.QInputDialog.getText(self, 'Input', 
        #     'Enter Az Alt:')

        # Use formlayout to make the form
        equatorialgroup = ( [('Right Ascension', ''), ('Declination', '')], "Equatorial", "Input equatorial coordinates." )
        horizontalgroup = ( [('Azimuth',''), ('Altitude','')], "Horizontal", "Input Horizontal coordinates." )
        galacticgroup   = ( [('Longitude', ''), ('Latitude', '')], "Galactic", "Input galactic coordinates." )

        result = fedit([equatorialgroup, horizontalgroup, galacticgroup])
        print result
        if result:

            # Need to parse the output of the form
            skycoord = self._parseInput(result)
            if skycoord:
                #self.parent().srt.slew(self.parent().skymap,(azf,elf))
                currentPos = self.parent().drive.skycoord()
                targetPos = skycoord
                print targetPos
                if targetPos == currentPos:
                        print("Already at that position.")
                        #self.targetPos = currentPos
                        self.parent().skymap.setTargetPos(currentPos)
                else:
                        print("Slewing to " + str(targetPos))
                        self.parent().skymap.setTargetPos(targetPos)
                        self.parent().drive.goto(targetPos)
                        #self.parent().skymap.setCurrentPos(targetPos)
                        #self.parent().updateStatusBar()
        self.parent().setFocus()
                
    def handleTrackButton(self):
        """
        Whenever the track button is pressed, the SRT will begin tracking whatever source is currently seclected.  If it is pressed again and the source hasn't changed, it'll stop tracking that source.
        """
        if self.trackToggle == TrackToggle.OFF:
            self.trackToggle = TrackToggle.ON
            print("Track Toggle ON")
            self.parent().drive.track()
        elif self.trackToggle == TrackToggle.ON:
            self.trackToggle = TrackToggle.OFF
            print("Track Toggle OFF")
            self.parent().drive.track(tracking=False)
        self.parent().setFocus()

    def handleCalibrateButton(self):
        self.parent().drive.calibrate()
        self.parent().setFocus()

    def getSlewToggle(self):
        return self.slewToggle

    def setSlewToggle(self,st):
        self.slewToggle = st

def readConfigFile():
    pass

def writeConfigFile():
    pass
    

def park():
    """
    A simple script to park the telescope in the stow position.
    """
    import sys

    import time
    import drive

    device = config.get('arduino','dev')
    print "Connecting to the drive" 
    connection = drive.Drive(device, config.get("arduino", "baud"), simulate=0, homeonstart=False)
    print "Connected"
    
    #connection.stow()

    if sys.argv[1] == "snow":
        # If we're parking due to snow we want to park in the home position
        # to avoid the bowl filling with the white stuff
        command = connection.home()
        #while connection.homing ==True: 
        #    print "Homing..."
        #    time.sleep(1)

    elif sys.argv[1] == "wind":
        # If we're parking due to the wind then park in the stow position
        # pointing straight up
        connection._command(connection.vocabulary['STOW'])
        time.sleep(1)
        #connection.stow()

    

def main():
    app = QtGui.QApplication(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('-live',dest='live',action='store_true',
                        help='Starts main in live mode.')
    parser.add_argument('-sim',dest='sim',action='store_true',
                        help='Starts main in simulation mode.')
    args = parser.parse_args()
    if args.live == False and args.sim == True:
        print("Simulation mode enabled.")
        mode = Mode.SIM
    else:
        mode = Mode.LIVE

    device = config.get('arduino','dev')
    catalogue = config.get('catalogue','catfile')
    calibrationSpeeds = config.get('calibration','speeds')
    homeOffset = config.get('offsets','home')
    #calibrationSpeeds = (cs.split()[0],cs.split()[1])
    #print(calibrationSpeeds.split()[0],calibrationSpeeds.split()[1])

    if mode == Mode.SIM:
        drive = Drive(simulate=1,calibration=calibrationSpeeds)
    elif mode == Mode.LIVE:
        drive = Drive(simulate=0,calibration=calibrationSpeeds, persist=True)
    
    main = mainWindow(drive,catalogue)

    main.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

   
 
   
