"""
Container class for a radio source.
Author: Ronnie Frith
Contact: frith.ronnie@gmail.com
"""

import astropy, math
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS, Galactic
import time, ephem


class RadioSource():
    """
    A container class for a radio source - holds position and other relevant information given by astropy and/or pyephem.
    """
    def __init__(self,name):
        self.pos = (0,0) # (az,alt)
        self.name = name
        self.acreRoadAstropy = EarthLocation(lat=55.9024278*u.deg,lon=-4.307582*u.deg,height=61*u.m)
        self.exists = False
        
        self.acreRoadPyEphem = ephem.Observer()
        self.acreRoadPyEphem.lon, self.acreRoadPyEphem.lat = '-4.3', '55.9'   #glasgow

    def sun(self):
        self.acreRoadPyEphem.date = ephem.now()
        sun = ephem.Sun()
        sun.compute(self.acreRoadPyEphem)
        az = float(repr(sun.az))*(180/math.pi) # quick hack to go from DEG:ARCMIN:ARCSEC to 00.00 degs
        alt = float(repr(sun.alt))*(180/math.pi)
        self.pos = (az,alt)
        self.exists = True

    def moon(self):
        self.acreRoadPyEphem.date = ephem.now()
        moon = ephem.Moon()
        moon.compute(self.acreRoadPyEphem)
        az = float(repr(moon.az))*(180/math.pi) 
        alt = float(repr(moon.alt))*(180/math.pi)
        self.pos = (az,alt)
        self.exists = True
        

    def lookupAstropy(self):
        """
        Searches for the source CDS name to get current position in azalt relative to Acre Road.
        """
        self.exists = False
        try:
            source = SkyCoord.from_name(self.name)
        except astropy.coordinates.name_resolve.NameResolveError:
            return False
        self.exists = True
        now = Time(time.time(),format='unix')
        altazframe = AltAz(obstime=now,location=self.acreRoadAstropy)
        sourcealtaz = source.transform_to(altazframe)
        self.pos = (float(sourcealtaz.az.degree),float(sourcealtaz.alt.degree))
        return True

    def update(self):
        """
        Update current position of the source.
        """
        if self.name.lower() == "sun":
            self.sun()
        elif self.name.lower() == "moon":
            self.moon()
        else:
            source = SkyCoord.from_name(self.name)
            now = Time(time.time(),format='unix')
            altazframe = AltAz(obstime=now,location=self.acreRoadAstropy)
            sourcealtaz = source.transform_to(altazframe)
            self.pos = (float(sourcealtaz.az.degree),float(sourcealtaz.alt.degree))

    def isVisible(self):
        """
        """
        (alt,az) = self.pos
        if alt < 0.0:
            return False
        else:
            return True

    def getExists(self):
        return self.exists

    def setExists(self, tf):
        self.exists = tf

    def getPos(self):
        return self.pos

    def setPos(self,pos):
        self.pos = pos
        
    def getName(self):
        return self.name

    def setName(self,name):
        self.name = name



def radec(azel):
    """
    Return current coordinate in right ascention and declination.
    """
    (az,el) = azel
    now = Time(time.time(),format='unix')
    acreRoad = EarthLocation(lat=55.9*u.deg,lon=-4.3*u.deg,height=61*u.m) # change this
    azelframe = AltAz(az*u.deg,el*u.deg,obstime=now,location=acreRoad)
    source = SkyCoord(azelframe)
    radecframe = ICRS()
    radec = source.transform_to(radecframe)
    return (float(radec.ra.hour),float(radec.dec.degree))


def galactic(azel):
    return (0.00,0.00)
