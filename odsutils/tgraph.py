# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license.

from astropy.time import Time, TimeDelta
from datetime import datetime, timedelta
from numpy import argmin, round, ceil, floor
from odsutils import ods_timetools as timetools


INTERPRETABLE_DATES = ['now', 'current', 'today', 'yesterday', 'tomorrow']
DAYSEC = 24 * 3600
SIDEREAL_RATE = 23.93447

class Graph:
    def __init__(self, title="Graph"):
        self.title = title

    def setup(self, start, dt_min=10.0, duration_days=1.0):
        start = timetools.interpret_date(start, fmt='datetime')
        daystart = timetools.interpret_date(timetools.interpret_date(start, '%Y-%m-%d'), fmt='datetime')
        self.start = Time(daystart.replace(hour=start.hour))
        self.end = self.start + TimeDelta(duration_days * DAYSEC, format='sec')
        self.T = duration_days
        self.N = int(self.T * DAYSEC / (dt_min * 60.0)) + 1

    def ticks_labels(self, tz, location, rowhdr, int_hr=2):
        self.rowhdr = rowhdr
        self.rows = []
        self.current = self.cursor_position_t(timetools.interpret_date('now', fmt='Time'), round)
        self.show_current = self.current > -1 and self.current <= self.N
        utc_t = Time([self.start + TimeDelta(int(x)*3600.0, format='sec') for x in range(0, 26, int_hr)], scale='utc')
        self.lst = utc_t.sidereal_time('mean', longitude=location)
        lstday = argmin(self.lst[:-1])
        lsteq = datetime(year=self.start.datetime.year, month=self.start.datetime.month, day=self.start.datetime.day,
                         hour=int(self.lst[0].hms.h), minute=int(self.lst[0].hms.m), second=int(self.lst[0].hms.s))
        if lstday: lsteq = lsteq - timedelta(days=1)
        elapsed = TimeDelta(((utc_t - utc_t[0]).to('second').value) * (1.0 - SIDEREAL_RATE/24.0), format='sec')
        lst_l = Time([Time(lsteq.replace(minute=0, second=0, microsecond=0)) + TimeDelta(int(x)*3600.0, format='sec') for x in range(0, 27, int_hr)])
        lstoff = (Time(lsteq) - lst_l[0]) - elapsed
        utc_l = utc_t - TimeDelta(lstoff, format='sec')
        self.tzorder = ['UTC', 'LST']
        self.tzinfo = {'UTC': 0.0, 'LST': lstoff}
        self.ticks = {'UTC': {'utc': utc_t,
                              'times': utc_t,
                              'current': '@'},
                      'LST': {'utc': utc_l,
                              'times': lst_l,
                              'current': '@'}}
        if tz.upper() != 'UTC':
            tz, tzoff = timetools.get_tz(tz, self.start)
            self.tzorder = ['UTC', tz, 'LST']
            self.tzinfo[tz] = tzoff
            self.ticks[tz] = {'utc': utc_t,
                              'times': utc_t + TimeDelta(self.tzinfo[tz] * 3600.0, format='sec'),
                              'current': '@'}
        for this_tz in self.tzinfo:
            self.ticks[this_tz]['labels'] = [' '] * (self.N + 1)
            self.ticks[this_tz]['ticks'] =[' '] * (self.N + 1)
            for i in range(len(utc_t)):
                toff = self.cursor_position_t(self.ticks[this_tz]['utc'][i], func=round)
                if toff < 0 or toff > self.N:
                    continue
                self.ticks[this_tz]['ticks'][toff] = '|'
                self.ticks[this_tz]['labels'][toff] = f"{self.ticks[this_tz]['times'][i].datetime.hour:02d}"
            if self.show_current:
                self.ticks[this_tz]['ticks'][self.current] = self.ticks[this_tz]['current']

    def cursor_position_t(self, t, func):
        dt = (t - self.start).to('day').value
        return int(func( (dt/self.T) * self.N) )

    def row(self, estart=None, estop=None):
        row = ['.'] * (self.N + 1)
        if estart is None or estop is None:
            pass
        else:
            starting = 0 if estart < self.start else self.cursor_position_t(estart, func=floor)
            ending = self.N if estop > self.end else self.cursor_position_t(estop, func=ceil)
            for star in range(starting, ending):
                row[star] = '*'
        if self.show_current:
            row[self.current] = '@'
        self.rows.append(row)

    def make_table(self):
        import tabulate
        tabulate.PRESERVE_WHITESPACE = True
        maxrhdr = 4 if (self.rowhdr is None or self.rowhdr[0] is None) else max([len(x[1]) for x in self.rowhdr])
        self.g_info = {'width': [2, maxrhdr] + [1] * (self.N+1), 'rows': []}
        for this_tz in self.tzorder:
            if this_tz == 'LST': continue
            self.g_info['rows'].append([' ', this_tz] + self.ticks[this_tz]['labels'])
        self.g_info['rows'].append([' ', ' '] + self.ticks['UTC']['ticks'])
        for i, row in enumerate(self.rows):
            srh = ' ' if self.rowhdr[i] is None else self.rowhdr[i][1]
            enh = ' ' if self.rowhdr[i] is None else self.rowhdr[i][0]
            self.g_info['rows'].append([enh, srh] + row)
        self.g_info['rows'].append([' ', ' '] + self.ticks['LST']['ticks'])
        self.g_info['rows'].append([' ', 'LST'] + self.ticks['LST']['labels'])

        table = []
        for rowstr in self.g_info['rows']:
            d0 = [x[0] for x in rowstr[2:]] + [' ']
            d1 = [' '] + [x[1] if len(x) > 1 else ' ' for x in rowstr[2:]]
            xx = [aa if aa != ' ' else bb for aa, bb in zip(d0, d1)]
            this_row = [rowstr[0], rowstr[1], ''.join(xx)]
            table.append(this_row)
        self.tabulated = tabulate.tabulate(table, tablefmt='plain', colalign=('right', 'right', 'left'))
