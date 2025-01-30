from copy import copy
from .ods_standard import Standard
from . import ods_tools as tools
from . import ods_timetools as timetools
from numpy import floor


DEFAULT_WORKING_INSTANCE = 'primary'
PLOT_AZEL = 'Az vs El'
PLOT_TIMEEL = 'Time vs El'
REF_LATEST_TIME = timetools.interpret_date('2026-12-31T23:59', fmt='Time')
REF_EARLIEST_TIME = timetools.interpret_date('2020-01-01T00:00', fmt='Time')


class ODSInstance:
    """Light class containing the data, some core classes and metadata -- most handling is done within ODS."""

    def __init__(self, instance_name, version='latest'):
        """
        Parameters
        ----------
        instance_name : str
            Name of instance -- the key used in ODS
        version : str
            Standard version to use.

        """
        self.instance_name = instance_name
        self.standard = Standard(version=version)
        self.input = 'init'
        self.entries = []
        self.valid_records = []
        self.invalid_records = {}
        self.number_of_records = 0
        self.input_sets = {'invalid': set()}

    def new_record(self, entry={}, defaults={}):
        """
        Add a new record, with each value set to None, then apply defaults, then new fields and append to entries.

        Parameter
        ---------
        defaults : dict
            Dictionary containing default values
        fields : dict
            Dictionary containing new fields.

        """
        rec = {}
        for key in self.standard.ods_fields:
            val = None
            if key in entry:
                val = entry[key]
            elif key in defaults:
                val = defaults[key]
            rec[key] = self.dump(key, val, fmt='InternalRepresentation')
        self.entries.append(rec)

    def read(self, ods_input):
        """
        Read in an existing ods file or dictionary and pull out input sets.

        Checking is done in ODS (arguably should probably be done here)

        Parameter
        ---------
        ods_input : str or dict
            Name of ods json file or dict

        Attributes
        ----------
        input : str
            The supplied ods file name or source
        entries : list
            List of ods records that is manipulated
        number_of_records : int
            Number of records in ods instance
        input_sets : set
            List of input sets and invalid keys -- set in gen_info
        number_of_records : int
            Number of records (entries) -- set in gen_info

        """
        if isinstance(ods_input, dict):
            input_ods_data = ods_input
            self.input = 'dictionary'
        elif isinstance(ods_input, str):
            if ods_input.startswith('http'):
                input_ods_data = tools.get_url(ods_input, fmt='json')
            else:
                input_ods_data = tools.read_json_file(ods_input)
            self.input = ods_input 
        else:
            return False

        if self.standard.data_key in input_ods_data:
            input_ods_data = input_ods_data[self.standard.data_key]
        self.entries += self.dump('all', input_ods_data, fmt='InternalRepresentation')
        self.gen_info()
        return True

    def gen_info(self):
        """
        Get some extra info on the instance.

        Attributes
        ----------
        valid_records : list
            List of valid record entry numbers
        invalid_record : dict
            Dict of invalid records, keyed on entry number
        input_sets : set
            List of input sets and invalid keys -- set in gen_info
        number_of_records : int
            Number of records (entries) -- set in gen_info
        earliest : Time
            Time of earliest record
        latest : Time
            Time of latest record

        """
        self.earliest = REF_LATEST_TIME
        self.latest = REF_EARLIEST_TIME
        self.number_of_records = len(self.entries)
        self.invalid_records = {}
        self.valid_records = []
        for ctr, entry in enumerate(self.entries):
            for key, val in entry.items():
                if key in self.standard.ods_fields:
                    self.input_sets.setdefault(key, set())
                    self.input_sets[key].add(val)
                    if key == self.standard.start and entry[key] < self.earliest:
                        self.earliest = copy(entry[key])
                    elif key == self.standard.stop and entry[key] > self.latest:
                        self.latest = copy(entry[key])
                else:
                    self.input_sets['invalid'].add(key)
            is_valid, msg = self.standard.valid(entry)
            if is_valid:
                self.valid_records.append(ctr)
            else:
                self.invalid_records[ctr] = msg

    def dump(self, key, val, fmt='isoformat'):
        """
        Prep entry/entries for dumping to file or internal.

        Parameters
        ----------
        key : str
            key of the entry or 'all'
        val : *
            value of the entry or a list of entries if key == 'all'
        fmt : str
            Format infomation, primarily for time
    
        Return
        ------
        value or dict, or list of dict
        """
        fmt = 'Time' if fmt == 'InternalRepresentation' else fmt
        fmt = 'isoformat' if fmt == 'ExternalFormat' else fmt
        if key == 'all':
            if isinstance(val, list):
                entries = []
                for entry in val:
                    entries.append(self.dump('all', entry, fmt=fmt))
                return entries
            elif isinstance(val, dict):
                this_entry = {}
                for tkey, tval in val.items():
                    this_entry[tkey] = self.dump(tkey, tval, fmt=fmt)
                return this_entry
        elif key in self.standard.time_fields:
            return timetools.interpret_date(val, fmt=fmt)
        else:
            return val

    def view(self, order=['src_id', 'src_start_utc', 'src_end_utc'], number_per_block=5):
        """
        View the ods instance as a table arranged in blocks.

        Parameters
        ----------
        order : list
            First entries in table, rest of ods record values are appended afterwards.
        number_per_block : int
            Number of records to view per block

        """
        if not self.number_of_records:
            return
        from tabulate import tabulate
        from numpy import ceil
        blocks = [range(i * number_per_block, (i+1) * number_per_block) for i in range(int(ceil(self.number_of_records / number_per_block)))]
        blocks[-1] = range(blocks[-1].start, self.number_of_records)
        order = order + [x for x in self.standard.ods_fields if x not in order]
        for blk in blocks:
            header = ['Field    \    #'] + [str(i) for i in blk]
            data = []
            for key in order:
                row = [key] + [self.dump(key, self.entries[i][key], fmt='isoformat') for i in blk]
                data.append(row)
            tble = tabulate(data, headers=header)
            print(tble)
            print('=' * len(tble.splitlines()[1]))
    
    def graph(self, location='ATA', numpoints=160, numticks=10):
        """
        Text-based graph of ods times/targets sorted by start/stop times.

        Parameters
        ----------
        numpoints : int
            Number of points to use.
        numticks : int
            Number of interior ticks -- not used yet.

        """
        from . import tgraph, locations
        sorted_ods = tools.sort_entries(self.entries, [self.standard.start, self.standard.stop], collapse=False, reverse=False)
        loc = locations.Location(location)
        rowhdr = [[i, x['src_id']] for i, x in enumerate(sorted_ods)]
        graph = tgraph.Graph()
        graph.setup(self.earliest, duration_days=(self.latest - self.earliest).jd)
        graph.ticks_labels(tz=loc.tz, location=loc.loc, rowhdr=rowhdr, int_hr=2)
        for entry in sorted_ods:
            graph.row(entry['src_start_utc'], entry['src_end_utc'])
        graph.make_table()
        print(graph.tabulated)

    def write(self, file_name):
        """
        Export the ods instance to an ods json file.

        Parameter
        ---------
        file_name : str
            Name of ods json file to write

        """
        entries = self.dump('all', self.entries, fmt='ExternalFormat')
        tools.write_json_file(file_name, {self.standard.data_key: entries})

    def export2file(self, filename, cols='all', sep=','):
        """
        Export the ods to a data file.

        Parameters
        ----------
        file_name : str
            Name of data file
        cols : str ('all', csv-list) or list
            List of entry keys
        sep : str
            Separator to use

        """
        entries = self.dump('all', self.entries, fmt='ExternalFormat')
        cols = list(self.standard.ods_fields.keys()) if cols == 'all' else tools.listify(cols)
        tools.write_data_file(filename, entries, cols, sep=sep)
