from . import ods_tools as tools
from . import ods_timetools as timetools
from . import logger_setup, __version__
from astropy.time import TimeDelta
from datetime import datetime, timedelta
import logging
from . import LOG_FILENAME, LOG_FORMATS

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class ODSCheck:
    """
    Utilities to check ODS instances/records.

    """
    def __init__(self, standard=None, conlog='INFO', filelog=False, **kwargs):
        """
        Parameter
        ---------
        standard : str
            Standard to use
        conlog : str or bool
            Log level for conole logging
        filelog : str or bool
            Log level for file logging
        **kwargs : kept to catch old keywords

        """
        self.log_settings = logger_setup.Logger(logger, conlog=conlog, filelog=filelog, log_filename=LOG_FILENAME, path=None,
                                                filelog_format=LOG_FORMATS['filelog_format'], conlog_format=LOG_FORMATS['conlog_format'])
        logger.info(f"{__name__} ver. {__version__}")
        self.standard = standard

    def change_standard(self, standard):
        self.standard = standard
    
    def is_same(self, rec1, rec2, fields2check='all', standard=None):
        """
        Checks to see if two records are the same.

        Parameters
        ----------
        rec1 : dict
            ODS record
        rec2 : dict
            ODS record
        standard : Standard Class
            Standard to use

        Return
        ------
        bool : True if the entries are the same

        """
        standard = self.standard if standard is None else standard
        if fields2check == 'all':
            fields2check = standard.ods_fields
        for key in fields2check:
            try:
                if str(rec1[key]) != str(rec2[key]):
                    return False
            except KeyError:  # Doesn't check across standards.
                return False
        return True

    def is_duplicate(self, ods, record, fields2check='all'):
        """
        Checks the ods for the record.

        Parameters
        ----------
        ods : ODS Instance
            ODS Instance to check
        record : dict
            Reord to check

        Return
        ------
        bool : True if the record is already in ODS Instance

        """
        for entry in ods.entries:
            if self.is_same(entry, record, fields2check==fields2check, standard=ods.standard):
                return True
        return False

    def observation(self, rec, el_lim_deg=10.0, dt_sec=120.0, show_plot=False, standard=None):
        """
        Determine whether an ODS record represents a source above the horizon.

        Parameters
        ----------
        rec : dict
            ODS record
        el_lim_deg : float
            Elevation limit that represents "above the horizon"
        dt_sec : float
            Time step for ephemerides check.
        show_plot : bool
            Show the plot of ephemerides.
        stanrdard : Standard or None
            Standard to use

        Return
        ------
        tuple or False
            False if never above the horizon, otherwise a tuple containing the limiting times within the record span.

        """
        from astropy.coordinates import EarthLocation, AltAz, SkyCoord
        import astropy.units as u
        from numpy import where

        standard = self.standard if standard is None else standard
        start = timetools.interpret_date(rec[standard.start], fmt='Time')
        stop = timetools.interpret_date(rec[standard.stop], fmt='Time')
        dt = TimeDelta(dt_sec, format='sec')
        times = []
        this_step = start
        while(this_step < stop):
            times.append(this_step)
            this_step += dt
        if not len(times):
            return times
        times = timetools.interpret_date(times, fmt='Time')
        location = EarthLocation(lat = float(rec[standard.lat]) * u.deg, lon = float(rec[standard.lon]) * u.deg, height = float(rec[standard.ele]) * u.m)

        aa = AltAz(location=location, obstime=times)
        coord = SkyCoord(float(rec[standard.ra]) * u.deg, float(rec[standard.dec]) * u.deg)
        obs = coord.transform_to(aa)
        above_horizon = where(obs.alt > el_lim_deg * u.deg)[0]
        if not len(above_horizon):
            return False
        if show_plot:
            import matplotlib.pyplot as plt
            plt.figure(standard.plot_azel)
            plt.plot(obs.az, obs.alt, label=rec[standard.source])
            plt.figure(standard.plot_timeel)
            plt.plot(times.datetime, obs.alt, label=rec[standard.source])
        return (times[above_horizon[0]].datetime.isoformat(timespec='seconds'), times[above_horizon[-1]].datetime.isoformat(timespec='seconds'))
    
    def continuity(self, ods, time_offset_sec=1, adjust='stop'):
        """
        Check whether records overlap.

        This assumes that the list is fairly reasonable and doesn't do anything very smart at this point.

        Parameters
        ----------
        ods : list
            ODS list of records
        time_offset_sec : float
            Time used to offset overlapping entries
        adjust : str
            Adjust 'start' or 'stop'

        Return
        ------
        Adjusted ODS list of records

        """
        if adjust not in ['start', 'stop']:
            logger.warning(f'Invalid adjust spec - {adjust}')
            return ods
        adjusted_entries = tools.sort_entries(ods, [ods.standard.start, ods.standard.stop])
        for i in range(len(adjusted_entries) - 1):
            this_stop = timetools.interpret_date(adjusted_entries[i][ods.standard.stop], fmt='Time')
            next_start = timetools.interpret_date(adjusted_entries[i+1][ods.standard.start], fmt='Time')
            if next_start < this_stop:  # Need to adjust
                if adjust == 'start':
                    next_start = this_stop + TimeDelta(time_offset_sec, format='sec')
                elif adjust == 'stop':
                    this_stop = next_start - TimeDelta(time_offset_sec, format='sec')
                adjusted_entries[i].update({ods.standard.stop: this_stop.datetime.isoformat()})
                adjusted_entries[i+1].update({ods.standard.start: next_start.datetime.isoformat()})
                if next_start < this_stop:
                    logger.warning(f"{self.pre}New start is before stop so still need to fix.")
        return adjusted_entries

    def coverage(self, ods):
        """
        Check coverage of records in an ODS instance.

        Parameter
        ---------
        ods : list
            ODS list of records

        Return
        ------
        float : fraction of time covered

        """
        from copy import copy

        sorted_entries = tools.sort_entries(ods.entries, [ods.standard.stop, ods.standard.start])
        times = []
        for entry in sorted_entries:
            times.append([entry[ods.standard.start].datetime, entry[ods.standard.stop].datetime])
        merged = merge_intervals(times)
        total_duration = timedelta(0)
        for start, end in merged:
            total_duration += (end - start)
        frac_cov = total_duration.total_seconds() / (merged[-1][1] - merged[0][0]).total_seconds()
        logger.info(f"Time covered: {total_duration} of {merged[-1][1]-merged[0][0]}  ({100.0 * frac_cov:.1}%)")
        return total_duration, merged

    def read_log_file(self, fname, tformat='%Y-%m-%d %H:%M:%S'):
        self.log_fname = fname
        self.log_data = {}
        with open(fname, 'r') as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                try:
                    time, msg = line.strip().split(',', 1)
                    time = datetime.strptime(time, tformat)
                    self.log_data[time] = msg
                except ValueError:
                    print(f"Invalid line in log file: {line.strip()}")
                    pass


def merge_intervals(intervals):
    """
    Merge overlapping intervals from a list of datetime tuples.

    Args:
        intervals (list of tuple): Each tuple is (start, end) where start and end are datetime objects.

    Returns:
        list of tuple: A list of merged intervals, each represented as (start, end).
    """
    if not intervals:
        return []
    
    # Sort intervals by their start times.
    intervals_sorted = sorted(intervals, key=lambda x: x[0])
    merged = []
    
    # Initialize the current interval to the first interval in the sorted list.
    current_start, current_end = intervals_sorted[0]
    
    for start, end in intervals_sorted[1:]:
        if start <= current_end:
            # Overlapping intervals: extend the current interval if necessary.
            current_end = max(current_end, end)
        else:
            # No overlap: add the current interval and start a new one.
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    
    # Append the last interval.
    merged.append((current_start, current_end))
    return merged
