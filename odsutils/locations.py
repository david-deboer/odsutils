import astropy.units as u
from astropy.coordinates import EarthLocation
import json


LOCATIONS = {
    'ata': EarthLocation(lat=40.817431*u.deg, lon=-121.470736*u.deg, height=1019*u.m)
}


class Location:
    def __init__(self, name='ata', tz='US/Pacific', loc=None, lat=None, lon=None, height=None):
        """
        This is a wrapper around the astropy.EarthLocation class, which is retained as the attribute 'loc'.

        Parameters
        ----------
        name : str
            Name of the location -- ignored if loc is a Location
        tz : str
            Timezone designator
        loc : EarthLocation or Location or None
            EarthLocation or Location instance or None
        lat : Quantity or None
            Latitude of the location, ignored if loc is supplied
        lon : Quantity or None
            Longitude of the location, ignored if loc is supplied
        height : Quantity or None
            Height of the location, ignored if loc is supplied

        """
        self.get_location(name=name, loc=loc, lat=lat, lon=lon, height=height)
        self.set_timezone(tz=tz)

    def __repr__(self):
        return self.stringify()
    
    def __str__(self):
        ss = ''
        for key, val in self.__dict__.items():
            if key not in ['loc']:
                ss += f"{key}: {val}\n"
        return ss

    def set_timezone(self, tz):
        """
        Set the timezone.

        Parameter
        ----------
        tz : str
            Timezone designator

        """
        self.tz = tz

    def set_coord(self, **kwargs):
        """
        Set the location coordinates.

        Parameters
        ----------
        kwarg : dict
            Keyword argument to pass to get_location

        """
        if 'unit' in kwargs:
            unit = u.Unit(kwargs['unit']) if isinstance(kwargs['unit'], str) else kwargs['unit']
            del(kwargs['unit'])
        for coord, val in kwargs.items():
            val = val if isinstance(val, u.Quantity) else float(val) * unit
            setattr(self, coord, val)

    def get_location(self, name=None, loc=None, lat=None, lon=None, height=0.0, latlon_unit='deg', height_unit='m'):
        """
        Parse location information to class.

        Parameters
        ----------
        name : str
            Name of the location -- ignored if loc is a Location
        loc : EarthLocation or Location or None
            EarthLocation or Location instance or None
        lat : float, Quantity or None
            Latitude of the location, ignored if loc is supplied
        lon : float, Quantity or None
            Longitude of the location, ignored if loc is supplied
        height : float, Quantity or None
            Height of the location, ignored if loc is supplied

        """
        if isinstance(name, Location):
            self.set_coord(lat=name.lat, lon=name.lon, height=name.height)
            self.name = name.name
            self.loc = name.loc
            return

        if isinstance(name, str) and name.lower() in LOCATIONS:
            loc =  LOCATIONS[name.lower()]

        if isinstance(loc, EarthLocation):
            self.set_coord(lat=loc.lat, lon=loc.lon, height=loc.height)
            self.name = name
            self.loc = loc
            return

        # Now handle non-EarthLocation/Location
        if loc is None and lat is None and isinstance(name, str):  # Given a stringified location in name
            loc = json.loads(name)
        elif isinstance(loc, str):  # Given a stringified location in loc
            loc = json.loads(loc)
        elif isinstance(name, dict):  # Given a dictionary in name
            loc = name
        if isinstance(loc, dict):
            lat = float(loc['lat'])
            lon = float(loc['lon'])
            height = float(loc['height'])
            name = loc['name']
        self.set_coord(lat=lat, lon=lon, unit=latlon_unit)
        self.set_coord(height=height, unit=height_unit)
        self.loc = EarthLocation(lat=self.lat, lon=self.lon, height=self.height)
        self.name = name

    def stringify(self):
        return json.dumps({'name': self.name, 'tz': self.tz,
                           'lat': self.lat.to_value('deg'), 'lon': self.lon.to_value('deg'), 'height': self.height.to_value('m')})