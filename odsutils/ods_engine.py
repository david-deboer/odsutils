from copy import copy
from .ods_standard import Standard
from .ods_check import ODSCheck
from .ods_tools import read_json_file, write_json_file, Base


class ODS(Base):
    """
    Utilities to read, update, write, and check ODS records.

    Maintains an internal self.ods record list that gets manipulated.

    """
    def __init__(self, quiet=False, version='latest'):
        self.quiet = quiet
        self.defaults = {}
        self.ods = []
        self.valid_records = []
        self.number_of_records = 0
        self.standard = Standard(version)  # Will modify/etc as NRAO defines
        self.check = ODSCheck(self.standard, self.quiet)

    def read_ods(self, ods_file_name):
        """
        Read in an existing ods file, check it and pull out input sets

        Parameter
        ---------
        ods_file_name : str
            Name of ods json file

        Attributes
        ----------
        ods_file_name : str
            The supplied ods file name
        ods : list
            List of ods records that is manipulated
        see self._gen_input_sets for others

        """
        self.ods_file_name = ods_file_name
        input_ods_data = read_json_file(self.ods_file_name)
        self.ods = input_ods_data[self.standard.data_key]  # This is the internal list of ods records
        self.number_of_records = len(self.ods)
        self.valid_records = self.check.ods(self.ods)
        self.qprint(f"Read {self.number_of_records} records from {self.ods_file_name}")
        number_of_invalid_records = self.number_of_records - len(self.valid_records)
        if number_of_invalid_records:
            print(f"{number_of_invalid_records} / {self.number_of_records} were not valid.")
        self._gen_input_sets()

    def _gen_input_sets(self):
        """
        Pull apart the existing valid ods records to get unique value sets

        Attribute
        ---------
        input_ods_sets : dict
            Dictionary of ods sets

        """
        self.input_ods_sets = {}  # 
        for irec in self.valid_records:
            for key, val in self.ods[irec].items():
                self.input_ods_sets.setdefault(key, set())
                self.input_ods_sets[key].add(val)

    def get_defaults_dict(self, defaults=':from_ods'):
        """
        Parameter
        ---------
        defaults : dict, str, None
            ods record default values (keys are standard.ods_fields)
            - dict provides the actual default key/value pairs
            - str 
              (a) if starts with ':', uses "special case" of the from_ods input sets (can add options...)
              (b) is a filename with the defaults as a json
                  if there is a ':', then it is that filename preceding and the key after the :
        
        Attribute
        ---------
        defaults : dict
            Dictionary containing whatever ods records defaults are provided.

        """
        if defaults is None:  # No change to existing self.defaults
            return
        if isinstance(defaults, dict):
            self.defaults = defaults
            using_from = 'input_dict'
        elif isinstance(defaults, str):
            using_from = defaults
            if defaults[0] == ':':
                if defaults[1:] == 'from_ods':
                    self.defaults = {}
                    for key, val in self.input_ods_sets.items():
                        if len(val) == 1:
                            self.defaults[key] = list(val)[0]
                else:
                    print(f"Not valid default case: {defaults}")
            else:
                fnkey = defaults.split(':')
                self.defaults = read_json_file(fnkey[0])
                if len(fnkey) == 2:
                    self.defaults = self.defaults[fnkey[1]]
        self.qprint(f"Default values from {using_from}")
        for key, val in self.defaults.items():
            self.qprint(f"\t{key:26s}  {val}")

    def update_by_elevation(self, el_lim_deg=10.0, dt_sec=120, show_plot=False):
        updated_ods = []
        for rec in self.ods:
            time_limits = self.check.observation(rec, el_lim_deg=el_lim_deg, dt_sec=dt_sec, show_plot=show_plot)
            if time_limits:
                valid_rec = copy(rec)
                valid_rec.update({self.standard.start: time_limits[0], self.standard.stop: time_limits[1]})
                updated_ods.append(valid_rec)
        self.ods = updated_ods
        self.number_of_records = len(self.ods)
        if show_plot:
            import matplotlib.pyplot as plt
            plt.figure(self.standard.plot_azel)
            plt.xlabel('Azimuth [deg]')
            plt.ylabel('Elevation [deg]')
            plt.axis(ymin = el_lim_deg)
            plt.legend()
            plt.figure(self.standard.plot_timeel)
            plt.xlabel('Time [UTC]')
            plt.ylabel('Elevation [deg]')
            plt.axis(ymin = el_lim_deg)
            plt.legend()

    def cull_ods_by_time(self, cull_time='now'):
        """
        Remove entries with end times before cull_time.  Overwrites self.ods.

        Parameter
        ---------
        cull_time : str
            isoformat time string

        """
        from astropy.time import Time
        if cull_time == 'now':
            cull_time = Time.now()
        else:
            cull_time = Time(cull_time)
        self.qprint(f"Culling ODS for {cull_time}:", end='  ')
        culled_ods = []
        for rec in self.ods:
            end_time = Time(rec['src_end_utc'])
            if end_time > cull_time:
                culled_ods.append(rec)
        self.ods = copy(culled_ods)
        self.qprint(f"retaining {len(self.ods)} of {self.number_of_records}")
        self.number_of_records = len(self.ods)
        self.valid_records = self.check.ods(self.ods)

    def cull_ods_by_invalid(self):
        """
        Remove entries that fail validity check.

        """
        self.qprint("Culling ODS for invalid records:", end='  ')
        self.valid_records = self.check.ods(self.ods)
        if len(self.valid_records) == self.number_of_records:
            self.qprint("retaining all.")
            return
        culled_ods = []
        for irec in self.valid_records:
            culled_ods.append(copy(self.ods[irec]))
        self.ods = culled_ods
        self.qprint(f"retaining {len(self.ods)} of {self.number_of_records}")
        self.number_of_records = len(self.ods)
        self.valid_records = self.check.ods(self.ods)

    def init_new_record(self):
        """
        Generate a full record, with each value set to None and apply defaults.

        Return
        ------
        dict
            A new initialized ods record

        """
        rec = {}
        for key in self.standard.ods_fields:
            rec[key] = None
        rec.update(self.defaults)
        return rec

    def add_new_record_from_namespace(self, ns, override=False):
        """
        Appends a new ods record to self.ods supplied as a Namespace
        
        Between defaults and namespace, must be complete/valid ods record unless override is True.

        """
        kwargs = {}
        for key, val in vars(ns).items():
            if key in self.standard.ods_fields:
                kwargs[key] = val
        self.add_new_record(override=override, **kwargs)

    def add_new_record(self, override=False, **kwargs):
        """
        Append a new record to self.ods, using defaults then kwargs.
        
        Between defaults and kwargs, must be complete/valid ods record unless override is True.

        """
        new_rec = self.init_new_record()
        new_rec.update(kwargs)
        is_valid = self.check.record(new_rec)
        if is_valid or override:
            self.ods.append(new_rec)
        else:
            self.qprint("WARNING: Record not valid -- not adding!")
        self.number_of_records = len(self.ods)

    def add_from_list(self, entries, override=False):
        """
        Append a new record to self.ods, using defaults then entries.
        
        Between defaults and entries, must be complete/valid ods record unless override is True.
        
        Parameters
        ----------
        entries : list of dicts
            List of dictionaries containing ODS fields
        override : bool
            add record regardless of passing ods checking

        """
        for entry in entries:
            self.add_new_record(override=override, **entry)
        self.qprint(f"Read {len(entries)} records from list.")
        self.valid_records = self.check.ods(self.ods)

    def add_from_file(self, data_file_name, override=False, sep="\s+", replace_char=None, header_map=None):
        """
        Append new records from a data file to self.ods; assumes the first line is a header.

        Between defaults and data file columns, must be a complete/valid ods record unless override is True.

        Parameters
        ----------
        data_file_name : str
            Name of input data file.
        override : bool
            add record regardless of passing ods checking
        sep : str
            separator
        replace_char : None, str, tuple, list
            replace characters in column headers
            - str: remove that character (replace with '')
            - tuple/list of length 1: same as above
            - tuple/list of length 2: replace [0] with [1]
        header_map : None, dict, str
            replace column header names with those provided
            - str: read json file
            - dict: {<datafile_header_name>: <ods_header_name>}

        """
        self.data_file_name = data_file_name
        import pandas as pd

        obs_list = pd.read_csv(self.data_file_name, sep=sep)

        if replace_char is not None:
            if isinstance(replace_char, str):
                replace_char = replace_char.split(',')
            if len(replace_char) == 1:
                replace_char.append('')
            obs_list.columns = obs_list.columns.str.replace(replace_char[0], replace_char[1])
        if header_map is not None:
            if isinstance(header_map, str):
                header_map = read_json_file(header_map)
            obs_list = obs_list.rename(header_map, axis='columns')

        for _, row in obs_list.iterrows():
            self.add_new_record(override=override, **row.to_dict())
        self.qprint(f"Read {len(obs_list.index)} records from {self.data_file_name}.")
        self.valid_records = self.check.ods(self.ods)

    def view_ods(self, order=['src_id', 'src_start_utc', 'src_end_utc'], number_per_block=5):
        """
        View the ods as a table arranged in blocks.

        Parameters
        ----------
        order : list
            First entries in table, rest of ods record values are append afterwards.
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
            data = []
            for key in order:
                row = [key] + [self.ods[i][key] for i in blk]
                data.append(row)
            print(tabulate(data))

    def write_ods(self, file_name):
        """
        Export the ods to an ods json file.

        Parameter
        ---------
        file_name : str
            Name of ods json file to write

        """
        if not len(self.ods):
            self.qprint("WARNING: Writing an empty ODS file!")
        write_json_file(file_name, {self.standard.data_key: self.ods})
