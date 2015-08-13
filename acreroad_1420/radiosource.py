"""
Container class for a radio source.
Author: Ronnie Frith
Contact: frith.ronnie@gmail.com
"""

import astropy, math
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS, Galactic
import time, ephem, datetime
import numpy as np
import ConfigParser

class RadioSource():
    """
    A container class for a radio source - holds position and other relevant information given by astropy and/or pyephem.
    """
    def __init__(self,name, location=None):
        self.pos = (0,0) # (az,alt)
        self.name = name
        config = ConfigParser.SafeConfigParser()
        config.read('settings.cfg')

        if not location:
            observatory = config.get('observatory', 'location').split()
            location = EarthLocation(lat=float(observatory[0])*u.deg, lon=float(observatory[1])*u.deg, height=float(observatory[2])*u.m)


        self.location = location

        self.exists = False
        
        self.acreRoadPyEphem = ephem.Observer()
        self.acreRoadPyEphem.lon, self.acreRoadPyEphem.lat = '-4.3', '55.9'   #glasgow

    def current_time_local(self):
        """                                                                                                                                  
        return the current local time                                                                                                        
        """
        return Time( datetime.datetime.now(), location = self.location)


    def sun(self):
        self.acreRoadPyEphem.date = ephem.now()
        sun = ephem.Sun()
        sun.compute(self.acreRoadPyEphem)
        az = float(repr(sun.az))*(180/math.pi) # quick hack to go from DEG:ARCMIN:ARCSEC to 00.00 degs
        alt = float(repr(sun.alt))*(180/math.pi)
        self.pos = (az,alt)
        now = self.current_time_local()
        altazframe = AltAz(az=az*u.degree, alt=alt*u.degree, obstime=now,location=self.location)
        self.skycoord = SkyCoord(altazframe)
        self.exists = True

    def moon(self):
        self.acreRoadPyEphem.date = ephem.now()
        moon = ephem.Moon()
        moon.compute(self.acreRoadPyEphem)
        az = float(repr(moon.az))*(180/math.pi) 
        alt = float(repr(moon.alt))*(180/math.pi)
        self.pos = (az,alt)
        now = self.current_time_local()
        altazframe = AltAz(az=az*u.degree, alt=alt*u.degree, obstime=now,location=self.location)
        self.skycoord = SkyCoord(altazframe)
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
        now = self.current_time_local()
        altazframe = AltAz(obstime=now,location=self.location)
        sourcealtaz = source.transform_to(altazframe)
        self.pos = (float(sourcealtaz.az.degree),float(sourcealtaz.alt.degree))
        self.skycoord = sourcealtaz
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
            now = self.current_time_local()
            altazframe = AltAz(obstime=now,location=self.location)
            sourcealtaz = source.transform_to(altazframe)
            self.pos = (float(sourcealtaz.az.degree),float(sourcealtaz.alt.degree))
            self.skycoord = sourcealtaz

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
    now = Time( datetime.datetime.now(), location = self.location)

    acreRoad = EarthLocation(lat=55.9*u.deg,lon=-4.3*u.deg,height=61*u.m) # change this
    azelframe = AltAz(az*u.deg,el*u.deg,obstime=now,location=acreRoad)
    source = SkyCoord(azelframe)
    radecframe = ICRS()
    radec = source.transform_to(radecframe)
    return (float(radec.ra.hour),float(radec.dec.degree))


def galactic(azel):
    return (0.00,0.00)


    
class GalacticPlane():
    points = []
    def __init__(self,time=None, location=None):
        self.time = time
        self.location = location
        self.update()

    def update(self, n=50):
        # We want to calculate the AltAz positions of the galactic plane
        
        c = SkyCoord([i for i in np.linspace(0, 360, n)], [0 for i in np.linspace(-90, 90.0, n)], frame="galactic", unit="deg", obstime = self.time, location=self.location)
        c = c.transform_to(AltAz(obstime=self.time,location=self.location))

        points = []
        for point in c:
            if point.alt.value > -10:
                points.append((point.az.value, point.alt.value))
        
        self.points = points

                
