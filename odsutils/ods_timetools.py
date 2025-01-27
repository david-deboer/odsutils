from astropy.time import Time, TimeDelta
from zoneinfo import available_timezones, ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime


def all_timezones():
    """
    Return 2 dictionaries:
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


def same_date(t1, t2, timespec='day'):
    """
    Return bool on equality of e1 == e2 for timespec.

    Parameters
    ----------
    t1 : interp_date
        Date to be checked
    t2 : interp_date
        Date to be checked
    timespec : str
        Precision of check
    
    """
    t1 = interpret_date(t1, fmt='Time')
    t2 = interpret_date(t2, fmt='Time')
    if timespec == 'exact':
        return t1 == t2
    fs = {'year': '%Y', 'month': '%Y-%m', 'day': '%Y-%m-%d',
          'hour': '%Y-%m-%dT%H', 'minute': '%Y-%m-%dT%H:%M', 'second': '%Y-%m-%dT%H:%M:%S'}
    return t1.datetime.strftime(fs[timespec]) == t2.datetime.strftime(fs[timespec])

def truncate_to_day(td):
    td = interpret_date(td, fmt='Time')
    return datetime(year=td.datetime.year, month=td.datetime.month, day=td.datetime.day)

def interpret_date(iddate, fmt='%Y-%m-%d'):
    """
    Interpret 'iddate' and return time or formated string.

    Parameters
    ----------
    iddate : datetime, Time, str, list
        Day to be interpreted
    fmt : str
        Either a datetime format string (starting with %) or 'Time'

    Return
    ------
    Time or str depending on fmt

    """
    if isinstance(iddate, list):
        iddate = [interpret_date(x, fmt=fmt) for x in iddate]
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
    elif len(str(iddate)) == 7:  # assume YYYY-MM
        iddate = Time(f"{iddate}-01")
    else:
        try:
            iddate = Time(iddate)
        except ValueError:
            iddate = None
    if iddate is not None and fmt[0] == '%':
        iddate = iddate.datetime.strftime(fmt)
    elif iddate is not None and fmt == 'datetime':
        iddate = iddate.datetime
    elif iddate is not None and fmt == 'isoformat':
        iddate = iddate.datetime.isoformat(timespec='seconds')
    return iddate

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


def strip_tz(this_datetime):
    if not isinstance(this_datetime, str):
        return this_datetime
    try:
        if this_datetime[-6] in ['+', '-']:
            return this_datetime[:-6]
    except IndexError:
        pass
    return this_datetime


def create_tz(tz, default='server', only_from_datetime=False):
    if isinstance(default, str):
        if default.lower() == 'server':
            default = datetime.datetime.now().astimezone().tzinfo
        elif default.lower() == 'utc':
            default = datetime.timezone(datetime.timedelta(0), 'UTC+00:00')
    if tz is None:
        return default
    if isinstance(tz, datetime.datetime):
        return tz.tzinfo
    if isinstance(tz, datetime.timezone):
        return tz

    if isinstance(tz, str) and ':' in tz:  # Provided as e.g. -08:00 or +02:00 or isoformat with tz
        if len(tz) == 6:
            sgn = tz[0]            
            hr, mn = [float(x) for x in tz[1:].split(':')]
        else:
            try:
                sgn = tz[-6]
                if sgn not in ['+', '-']:
                    return default
                hr, mn = [float(x) for x in tz[-6:].split(':')]
            except (IndexError, ValueError):
                return default
        vsgn = 1.0 if sgn == '+' else -1.0
        hroffset = vsgn * (hr + mn / 60.0)
        name = f"UTC{tz}"
    elif not only_from_datetime:
        from math import modf
        try:
            tz = float(tz)
        except (ValueError, TypeError):
            return default
        sgn = '-' if tz < 0.0 else '+'
        vsgn = 1.0 if sgn == '+' else -1.0
        hroffset = tz
        fhr, hr = modf(abs(tz))
        name = f"UTC{sgn}{int(hr):02d}:{int(60.0*fhr):02d}"
    else:
        return None
    return datetime.timezone(datetime.timedelta(hours=hroffset), name)


def make_datetime(**kwargs):
    """
    Take various datetime/str/offset/timezone options and return timezone-aware datetimes

    """
    for ptype in ['date', 'time', 'datetime', 'datestamp', 'timestamp', 'offset',
                  'tstart', 'tstop', 'tle', 'expected']:
        if ptype in kwargs:
            datetimes = kwargs[ptype]
            break
    else:
        raise ValueError("No valid datetime term included")
    if isinstance(datetimes, str):
        datetimes = datetimes.split(',')
    elif not isinstance(datetimes, list):
        datetimes = [datetimes]

    timezones = None
    for p in ['timezone', 'tz']:
        if p in kwargs:
            timezones = kwargs[p]
            break
    if isinstance(timezones, str):
        timezones = timezones.split(',')
    elif not isinstance(timezones, list):
        timezones = [timezones] * len(datetimes)

    if len(timezones) != len(datetimes):
        raise ValueError(f"Datetime lengths ({len(datetimes)}) differs from timezone lengths ({len(timezones)})")

    datetime_out = []
    for dt, tz in zip(datetimes, timezones):
        datetime_out.append(proc_datetime(dt, tz))

    if len(datetime_out) == 1:
        return datetime_out[0]
    else:
        return datetime_out


def proc_datetime(this_datetime, this_timezone):
    """
    Handles one datetime/timezone pair

    """
    this_timezone = create_tz(this_timezone, default=None)
    if this_timezone is None:
        this_timezone = create_tz(this_datetime, default='utc', only_from_datetime=True)

    # Process datetime value and timezone
    if this_datetime == 'now' or this_datetime is None:
        return datetime.datetime.now().astimezone(this_timezone)

    if isinstance(this_datetime, (float, int)):
        return datetime.datetime.now().astimezone(this_timezone) + datetime.timedelta(minutes=this_datetime)

    if isinstance(this_datetime, datetime.datetime):
        return this_datetime.replace(tzinfo=this_timezone)

    # ... it is a str, make sure no tz info left
    this_datetime = strip_tz(this_datetime)

    this_dt = None
    for this_tf in TIME_FORMATS:
        try:
            this_dt = datetime.datetime.strptime(this_datetime, this_tf)
            break
        except (TypeError, ValueError):
            try:
                if ':' in this_tf:
                    this_tf += ':%S'
                else:
                    this_tf += '%S'
                this_dt = datetime.datetime.strptime(this_datetime, this_tf)
                break
            except (TypeError, ValueError):
                try:
                    this_dt = datetime.datetime.strptime(this_datetime, this_tf+'.%f')
                    break
                except (TypeError, ValueError):
                    continue

    if isinstance(this_dt, datetime.datetime):
        return this_dt.replace(tzinfo=this_timezone)
    try:
        dt = float(this_datetime)
        return datetime.datetime.now().astimezone(this_timezone) + datetime.timedelta(minutes=dt)
    except (TypeError, ValueError):
        return None