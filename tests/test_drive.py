#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_drive
-----------------
Tests for the acreroad_1420.drive module
"""


import unittest

from acreroad_1420 import drive

class TestDrive(unittest.TestCase):
    def setUp(self):
        self.connection = drive.Drive('/dev/tty.usbserial', 9600, simulate=1)

    def testCalibrate(self):
        self.assertEqual(self.connection.calibrate(), ">c 000 000")

    def testCalibrateWithValues(self):
        self.assertEqual(self.connection.calibrate("450 650"), 1)

    def testClockSet(self):
        self.assertEqual(self.connection.setTime(), 1)

    def testLocationSet(self):
        self.assertEqual(self.connection.setLocation(), 1)

    def testLocationProvidedSet(self):
        from astropy.coordinates import EarthLocation
        import astropy.units as u
        bear_mountain = EarthLocation(lat=41.3*u.deg, lon=-74*u.deg, height=390*u.m)
        self.assertEqual(self.connection.setLocation(bear_mountain), 1)

    def testGotoSingle(self):
        from astropy.coordinates import SkyCoord
        from astropy.coordinates import ICRS, Galactic, FK4, FK5
        from astropy.coordinates import Angle, Latitude, Longitude
        import astropy.units as u

        c = SkyCoord(frame="galactic", l="1h12m43.2s", b="+1d12m43s")

        self.assertEqual(self.connection.goto(c), 1)

    def testHome(self):
        self.assertEqual(self.connection.home(), 1)
        
    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
