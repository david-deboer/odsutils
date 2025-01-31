from astropy.time import Time, TimeDelta
from zoneinfo import available_timezones, ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime


TUNITS = {'day': 24.0 * 3600.0, 'd': 24.0 * 3600.0,
          'hour': 3600.0, 'hr': 3600.0, 'h': 3600.0,
          'minute': 60.0,  'min': 60.0,  'm': 60.0,
          'second': 1.0, 'sec': 1.0, 's': 1.0}


def all_timezones():
    """
    Return 2 dictionaries, e.g.:
    1 - timezones['US/Pacific'] = ['PST', 'PDT]
    2 - tz_offsets['PST'] = [-8.0, -8.0...]  # they should all be the same...

    """
    timezones = {}
    tz_offsets = {}
    for tz_iana in available_timezones():
        try:
            this_tz = ZoneInfo(tz_iana)
            #
            t1 = datetime(year=2025, month=1, day=1, tzinfo=this_tz)
            this_tzname = t1.tzname()
            timezones[tz_iana] = [this_tzname]
            tz_offsets.setdefault(this_tzname, {'tz': [], 'offsets': []})
            tz_offsets[this_tzname]['tz'].append(tz_iana)
            tz_offsets[this_tzname]['offsets'].append(t1.utcoffset().total_seconds()/3600.0)
            #
            t2 = datetime(year=2025, month=7, day=1, tzinfo=this_tz)
            this_tzname = t2.tzname()
            timezones[tz_iana].append(this_tzname)
            tz_offsets.setdefault(this_tzname, {'tz': [], 'offsets': []})
            tz_offsets[this_tzname]['tz'].append(tz_iana)
            tz_offsets[this_tzname]['offsets'].append(t2.utcoffset().total_seconds()/3600.0)
        except ZoneInfoNotFoundError:
            continue
    return timezones, tz_offsets


def get_tz(tz='sys', dt='now'):
    """
    Returns tz_name, offset_hours

    """
    dt = interpret_date(dt, fmt='datetime')
    if tz == 'sys':
        tzinfo = dt.astimezone().tzinfo
        tz = tzinfo.tzname(dt)
        tzoff = tzinfo.utcoffset(dt).total_seconds()/3600.0
        return tz, tzoff
    timezones, tz_offsets = all_timezones()
    if tz in tz_offsets:
        return tz, tz_offsets[tz]['offsets'][0]
    if tz in timezones:
        this_tz = ZoneInfo(tz)
        dt = dt.replace(tzinfo=this_tz)
        return this_tz.tzname(dt), this_tz.utcoffset(dt).total_seconds() / 3600.0
    raise ValueError("Invalid timezone designation.")


def t_delta(t1, val, unit):
    dt = TimeDelta(val * TUNITS[unit], format='sec')
    t1 = interpret_date(t1, fmt='Time', NoneReturn=None)
    if t1 is None:
        return dt
    return t1 + dt


def interpret_date(iddate, fmt='Time', NoneReturn=None):
    """
    Interpret 'iddate' and return time or formated string.

    Parameters
    ----------
    iddate : datetime, Time, str, list
        Day to be interpreted
    fmt : str
        Either a datetime format string (starting with %) or 'Time', 'isoformat', 'datetime'
    NoneReturn : None or intepretable
        What to return if input is None

    Return
    ------
    Time or str depending on fmt

    """
    if iddate is None:
        return None if NoneReturn is None else interpret_date(NoneReturn, fmt=fmt)
    if isinstance(iddate, list):
        iddate = [interpret_date(x, fmt=fmt, NoneReturn=NoneReturn) for x in iddate]
        if fmt == 'Time':
            iddate = Time(iddate)
        return iddate
    if isinstance(iddate, str) and '/' in iddate:  # iddate +/- offset
        mult = {'d': 24.0*3600.0, 'h': 3600.0, 'm': 60.0, 's': 1.0}
        iddate, offs = iddate.split('/')
        iddate = interpret_date(iddate, fmt='Time')
        try:
            dt = mult[offs[-1]] * float(offs[:-1])
        except KeyError:
            dt = 60.0 * float(offs)  # default to minutes
        iddate += TimeDelta(dt, format='sec')
    if iddate == 'today' or iddate == 'now' or iddate == 'current':
        iddate = Time.now()
    elif iddate == 'yesterday':
        iddate = Time.now() - TimeDelta(24.0*3600.0, format='sec')
    elif iddate == 'tomorrow':
        iddate = Time.now() + TimeDelta(24.0*3600.0, format='sec')
    elif len(str(iddate)) == 4:  # assume just a year
        iddate = Time(f"{iddate}-01-01")
    elif isinstance(iddate, str) and len(iddate) == 7:  # assume YYYY-MM
        iddate = Time(f"{iddate}-01")
    else:
        try:
            iddate = Time(iddate)
        except ValueError:
            return NoneReturn
        
    if fmt[0] == '%':
        iddate = iddate.datetime.strftime(fmt)
    elif fmt == 'datetime':
        iddate = iddate.datetime
    elif fmt == 'isoformat':
        iddate = iddate.datetime.isoformat(timespec='seconds')
    elif fmt == 'jd':
        iddate = iddate.jd
    return iddate

def wait_until(target_time):
    """
    Pauses execution until the specified target time.

    Parameters:
    - target_time (datetime.datetime): The datetime to wait until.

    """
    from time import sleep
    now = datetime.datetime.now()
    target_time = interpret_date(target_time, fmt='datetime')

    if target_time <= now:
        print("CAREFUL TIME WAS BEFORE NOW")
        return
        #raise ValueError("Target time is in the past. Please provide a future time.")

    # Calculate the remaining time in seconds
    remaining_time = (target_time - now).total_seconds()
    print(f"Waiting for {remaining_time} seconds until {target_time}...")

    # Sleep for the remaining time
    sleep(remaining_time)
    print("Reached target time:", target_time)
    return remaining_time


#######################################OBSNERD
TIME_FORMATS = ['%Y-%m-%dT%H:%M', '%y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M', '%y-%m-%d %H:%M',
                '%Y/%m/%dT%H:%M', '%y/%m/%dT%H:%M',
                '%Y/%m/%d %H:%M', '%y/%m/%d %H:%M',
                '%d/%m/%YT%H:%M', '%d/%m/%yT%H:%M',
                '%d/%m/%Y %H:%M', '%d/%m/%y %H:%M',
                '%Y%m%dT%H%M', '%y%m%dT%H%M',
                '%Y%m%d %H%M', '%y%m%d %H%M',
                '%Y%m%d_%H%M', '%y%m%d_%H%M',
                '%Y%m%d%H%M', '%y%m%d%H%M'
            ]