from copy import copy
from .ods_check import ODSCheck
from . import ods_instance, logger_setup, __version__
from . import ods_tools as tools
from . import ods_timetools as timetools
import logging
from . import LOG_FILENAME, LOG_FORMATS

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

class ODS:
    """
    Utilities to handle ODS instances.

    The ODS instances are ods_instance.ODSInstance classes contained within the dictionary 'self.ods',
    each identified by a unique key (working_instance).  Unless a different instance is specified, the
    instance used is the one specified by 'self.working_instance, which is set to
    ods_instance.DEFAULT_WORKING_INSTANCE by default.

    The list of ODS records is stored in the 'entries' attribute of the ODSInstance class, and can be accessed
    using the 'self.ods[working_instance].entries' attribute.

    """
    def __init__(self, version='latest', working_instance=ods_instance.DEFAULT_WORKING_INSTANCE,
                 conlog='WARNING', filelog=False, **kwargs):
        """
        Parameters
        ----------
        version : str
            Version of default ODS standard -- note that instances can be different
        working_instance : str
            Key to use for the ods instance in use.
        conlog : str, False
            One of the logging levels for console: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        filelog : str, False
            One of the logging levels for file: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        **kwargs : kept to catch old keywords

        """
        self.log_settings = logger_setup.Logger(logger, conlog=conlog, filelog=filelog, log_filename=LOG_FILENAME, path=None,
                                                filelog_format=LOG_FORMATS['filelog_format'], conlog_format=LOG_FORMATS['conlog_format'])
        logger.info(f"{__name__} ver. {__version__}")

        # ###
        self.version = version
        self.ods = {}
        self.new_ods_instance(working_instance, version=version, set_as_working=True)
        self.defaults = {}
        self.check = ODSCheck(alert=self.log_settings.conlog, standard=self.ods[working_instance].standard)

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def write_ods(self, filename, adds=None, original=None, cull=['time', 'duplicate']):
        """
        This incorporates the "standard pipeline" of reading an existing ods file (original), adding new ones (adds),
        culling entries as indicated (cull) and writing the file (filename).

        A filename must be provided.
        If no 'adds' are provided, the working_instance is used.
        If no 'original' is provided, "adds" is the entire written ods, otherwise 'original' gets updated with 'adds'.
        Cull defaults to remove stale entries and duplicates, for no culling pass [].

        Parameters
        ----------
        filename : str
            ODS file to write
        adds : list or str or dict
            List of ods records to add or filename for records, or ods instance name, if None use self.working_instance
        original : str or None
            ODS file to read or URL to use, or ods instance name or None
        cull : list
            List of culling options to apply: 'time' for stale entries, 'duplicate' for duplicates

        """
        if adds is None:
            instance_to_add = self.working_instance
        elif isinstance(adds, str) and adds in self.ods.keys():
            instance_to_add = adds
        elif isinstance(adds, list):
            instance_to_add = 'instance_to_add'
            self.new_ods_instance(instance_name=instance_to_add)
            self.add_from_list(adds, instance_name=instance_to_add)
        elif isinstance(adds, dict):
            instance_to_add = 'instance_to_add'
            self.new_ods_instance(instance_name=instance_to_add)
            self.add_new_record(instance_name=instance_to_add, **adds)
        else:  # Assumes it is a filename of an ods file
            instance_to_add = 'instance_to_add'
            self.new_ods_instance(instance_name=instance_to_add)
            self.read_ods(adds, instance_name=instance_to_add)

        if original is None:
            instance_to_update = 'instance_to_update'
            self.new_ods_instance(instance_name=instance_to_update)
        elif original in self.ods.keys():
            instance_to_update = original
        else:
            instance_to_update = 'instance_to_update'
            self.new_ods_instance(instance_name=instance_to_update)
            self.read_ods(original, instance_name=instance_to_update)

        self.merge(from_ods=instance_to_add, to_ods=instance_to_update, remove_duplicates=True)

        pre_cull_num = copy(self.ods[instance_to_update].number_of_records)
        if 'time' in cull:
            self.cull_by_time('now', 'stale', instance_name=instance_to_update)
        if 'duplicate' in cull:
            self.cull_by_duplicate(instance_name=instance_to_update)
        if not self.ods[instance_to_update].number_of_records:
            logger.warning(f"Writing an empty ODS file!  Pre-cull count was {pre_cull_num}")
        self.ods[instance_to_update].write(filename)

    def new_ods_instance(self, instance_name, version='latest', set_as_working=False):
        """
        Create a blank ODS instance and optionally set as the working instance.

        Parameters
        ----------
        instance_name : str
            Name of instance.
        version : str
            Standard version to use.
        set_as_working : bool
            Flag to reset the working_instance to this instance_name.

        """
        self.ods[instance_name] = ods_instance.ODSInstance(
            instance_name = instance_name,
            version = version
        )
        if set_as_working:
            self.update_working_instance_name(instance_name)
    
    def update_working_instance_name(self, instance_name):
        """
        Update the class working_instance instance_name.
        
        Parameter
        ---------
        instance_name : str
            Name of instance

        """
        if instance_name in self.ods.keys():
            self.working_instance = instance_name
            logger.info(f"The ODS working instance is {self.working_instance}")
        else:
            logger.warning(f"ODS instance {instance_name} does not exist.")

    def get_instance_name(self, instance_name=None):
        """
        Return the class instance instance_name to use.
      
        Parameter
        ---------
        instance_name : str
            Name of instance

        Returns
        -------
        The instance name to use.
    
        """
        if instance_name is None:
            return self.working_instance
        if instance_name in self.ods:
            return instance_name
        logger.error(f"{instance_name} does not exist -- try making it with self.new_ods_instance or providing a different instance_name.")

    def read_ods(self, ods_input, instance_name=None):
        """
        Read in ods data from a file or input dictionary in same format.

        Parameters
        ----------
        ods_input : str
            ODS input, either filename or dictionary.
        instance_name : str, None
            Name of instance to use

        """
        instance_name = self.get_instance_name(instance_name)
        is_valid = self.ods[instance_name].read(ods_input)
        if not is_valid:
            logger.warning(f"Failed to read {ods_input} -- keeping empty instance.")
            return False
        logger.info(f"Read {self.ods[instance_name].number_of_records} records from {self.ods[instance_name].input}")
        self.instance_report(instance_name=instance_name)
        return True

    def instance_report(self, instance_name=None):
        instance_name = self.get_instance_name(instance_name)
        number_of_invalid_records = len(self.ods[instance_name].invalid_records)
        if self.ods[instance_name].number_of_records and number_of_invalid_records == self.ods[instance_name].number_of_records:
            logger.warning(f"All records ({self.ods[instance_name].number_of_records}) were invalid.")
        elif number_of_invalid_records:
            logger.warning(f"{number_of_invalid_records} / {self.ods[instance_name].number_of_records} were not valid.")
            for ctr, msg in self.ods[instance_name].invalid_records.items():
                logger.warning(f"Entry {ctr}:  {', '.join(msg)}")
        else:
            logger.info(f"{self.ods[instance_name].number_of_records} are all valid.")

    def get_defaults_dict(self, defaults='from_ods'):
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
            self.defaults = copy(defaults)
            defaults = 'input_dict'
        elif isinstance(defaults, str):
            if '.json' in defaults:
                fnkey = defaults.split(':')
                self.defaults = tools.read_json_file(fnkey[0])
                if len(fnkey) == 2:
                    self.defaults = self.defaults[fnkey[1]]
            elif defaults == 'from_ods':  # The only option for now, uses single-valued keys
                self.defaults = {}
                for key, val in self.ods[self.working_instance].input_sets.items():
                    if key != 'invalid' and len(val) == 1:
                        self.defaults[key] = list(val)[0]
            else:
                logger.warning(f"Not valid default case: {defaults}")
                return

        logger.info(f"Default values from {defaults}:")
        for key, val in self.defaults.items():
            logger.info(f"\t{key:26s}  {val}")

    def online_ods_monitor(self, url="https://www.seti.org/sites/default/files/HCRO/ods.json", logfile='online_ods_mon.txt', cols='all', sep=','):
        """
        Checks the online ODS URL against a local log to update for active records.  Typically used in a crontab to monitor
        the active ODS records posted.

        Parameters
        ----------
        url : str
            URL of online ODS server
        logfile : str
            Local logfile to use.
        cols : str('all', csv-list) or list
            Columns to write out.
        sep : str
            Separator to use in file.

        """
        self.new_ods_instance('from_web')
        self.read_ods(url, instance_name='from_web')
        self.cull_by_time(instance_name='from_web', cull_by='inactive')

        self.new_ods_instance('from_log')
        self.add_from_file(logfile, instance_name='from_log', sep=sep)
        self.merge('from_web', 'from_log', remove_duplicates=True)

        self.ods['from_log'].export2file(logfile, cols=cols, sep=sep)

    def check_active(self, ctime='now', read_from="https://www.seti.org/sites/default/files/HCRO/ods.json"):
        """Check which entry is active at ctime, if any."""
        self.new_ods_instance(instance_name='check_active')
        if isinstance(read_from, str):
            self.read_ods(read_from, instance_name='check_active')
        else:
            logger.info("Not reading new ODS instance for check_active.")
        ctime = timetools.interpret_date(ctime, fmt='Time')
        active = []
        for i, entry in enumerate(self.ods['check_active'].entries):
            if entry['src_start_utc'] <= ctime <= entry['src_end_utc']:
                active.append(i)
        return active


    ##############################################MODIFY#########################################
    # Methods that modify the existing self.ods

    def update_entry(self, entry, updates, instance_name=None):
        """
        Update the entry number with the updates dict values.

        Parameters
        ----------
        entry : int
            Number of entry to update
        updates : dict
            Dictionary containing the updates
        instance_name : str, None
            Instance to update

        """
        instance_name = self.get_instance_name(instance_name)
        updates = self.ods[instance_name].dump('all', updates, fmt='InternalRepresentation')
        if isinstance(entry, int):
            self.ods[instance_name].entries[entry].update(updates)
        else:
            logger.info('No other update entry options.')
            return
        self.ods[instance_name].gen_info()

    def update_by_elevation(self, el_lim_deg=10.0, dt_sec=120, instance_name=None, show_plot=False):
        """
        Check an ODS for sources above an elevation limit.  Will update the times for those above that limit.

        Parameters
        ----------
        el_lim_deg : float
            Elevation limit to use, in degrees.
        dt_sec : float
            Time step to use for check, in seconds.
        instance_name : str, None
            Name of instance to use
        show_plot : bool
            Flag to show a plot.

        """
        instance_name = self.get_instance_name(instance_name)
        logger.info(f"Updating {instance_name} for el limit {el_lim_deg}")
        updated_ods = []
        for rec in self.ods[instance_name].entries:
            time_limits = self.check.observation(rec, el_lim_deg=el_lim_deg, dt_sec=dt_sec, show_plot=show_plot)
            if time_limits and len(time_limits):
                valid_rec = copy(rec)
                valid_rec.update({self.ods[instance_name].standard.start: time_limits[0], self.ods[instance_name].standard.stop: time_limits[1]})
                updated_ods.append(valid_rec)
        self.ods[instance_name].entries = updated_ods
        self.ods[instance_name].gen_info()
        if show_plot:
            import matplotlib.pyplot as plt
            plt.figure(ods_instance.PLOT_AZEL)
            plt.xlabel('Azimuth [deg]')
            plt.ylabel('Elevation [deg]')
            plt.axis(ymin = el_lim_deg)
            plt.legend()
            plt.figure(ods_instance.PLOT_TIMEEL)
            plt.xlabel('Time [UTC]')
            plt.ylabel('Elevation [deg]')
            plt.axis(ymin = el_lim_deg)
            plt.legend()

    def update_by_continuity(self, time_offset_sec=1, adjust='start', instance_name=None):
        """
        Check the ODS for time continuity.  Not checked yet.

        Parameters
        ----------
        time_offset_set : int/float
            Spacing between record times.
        adjust : str
            Side to adjust start/stop
        instance_name : str, None
            Name of instance to use

        """
        instance_name = self.get_instance_name(instance_name)
        self.ods[instance_name].entries = self.check.continuity(self.ods[instance_name], time_offset_sec=time_offset_sec, adjust=adjust)
        self.ods[instance_name].gen_info()

    def update_ods_times(self, times=None, start=None, obs_len_sec=None, instance_name=None):
        """
        Reset the src_start_utc and src_stop_utc fields in self.ods.

        Parameter
        ---------
        times : list of lists/None or None
            If not None, each list item contains new start/stop for that record in the list or skip if None.
            Must be len(self.ods)
        start : str
            Start time in isoformat or 'now'
        obs_len_sec : str, list or None
            If 'start' is not None, this is the length/observation
            If list, must be len(self.ods)
        instance_name : str, None
            Name of instance to use

        """
        instance_name = self.get_instance_name(instance_name)
        if times is not None:
            if len(times) != self.ods[instance_name].number_of_records:
                logger.warning("times list doesn't have the right number of entries")
                return
        elif start is None or obs_len_sec is None:
            logger.warning("haven't specified enough parameters.")
            return
        else:
            if not isinstance(obs_len_sec, list):
                obs_len_sec = [obs_len_sec] * self.ods[instance_name].number_of_records
            elif len(obs_len_sec) != self.ods[instance_name].number_of_records:
                logger.warning("obs_len_sec doesn't have the right number of entries")
                return
            times = tools.generate_observation_times(start, obs_len_sec)
        for i, tt in enumerate(times):
            this_update = {self.ods[instance_name].standard.start: tt[0],
                           self.ods[instance_name].standard.stop: tt[1]}
            self.ods[instance_name].entries[i].update(this_update)
        self.ods[instance_name].gen_info()

    def cull_by_time(self, cull_time='now', cull_by='stale', instance_name=None):
        """
        Remove entries with end times before cull_time.  Overwrites self.ods[instance_name]

        Parameter
        ---------
        cull_time : str
            isoformat time string
        cull_for : str
            Either 'stale' or 'active'
        instance_name : str or None
            ODS instance

        """
        if cull_by not in ['stale', 'inactive']:
            logger.warning(f"Invalid cull parameter: {cull_by}")
            return
        instance_name = self.get_instance_name(instance_name)
        cull_time = timetools.interpret_date(cull_time, fmt='Time')
        logger.info(f"Culling ODS for {cull_time} by {cull_by}")
        culled_ods = []
        for rec in self.ods[instance_name].entries:
            stop_time = rec[self.ods[instance_name].standard.stop]
            add_it = True
            if cull_time > stop_time:
                add_it = False
            elif cull_by == 'inactive':
                start_time = rec[self.ods[instance_name].standard.start]
                if cull_time < start_time:
                    add_it = False
            if add_it:
                culled_ods.append(rec)
        self.ods[instance_name].entries = copy(culled_ods)
        self.ods[instance_name].gen_info()
        logger.info(f"retaining {len(self.ods[instance_name].entries)} of {self.ods[instance_name].number_of_records}")

    def cull_by_invalid(self,  instance_name=None):
        """
        Remove entries that fail validity check.

        Parameter
        ---------
        instance_name : str, None
            Name of instance to use

        """
        instance_name = self.get_instance_name(instance_name)
        self.ods[instance_name].gen_info()
        logger.info("Culling ODS for invalid records.")
        if not len(self.ods[instance_name].valid_records):
            logger.info("retaining all.")
            return
        starting_number = copy(self.ods[instance_name].number_of_records)
        culled_ods = []
        for irec in self.ods[instance_name].valid_records:
            culled_ods.append(copy(self.ods[instance_name].entries[irec]))
        self.ods[instance_name].entries = culled_ods
        self.ods[instance_name].gen_info()
        if not self.ods[instance_name].number_of_records:
            logger.warning("Retaining no records.")
        else:
            logger.info(f"retaining {self.ods[instance_name].number_of_records} of {starting_number}")
    
    def cull_by_duplicate(self, instance_name=None):
        """
        Remove duplicate entries, sorts it by the standard.sort_order_time

        """
        instance_name = self.get_instance_name(instance_name)
        logger.info("Culling ODS for duplicates")
        starting_number = len(self.ods[instance_name].entries)
        self.ods[instance_name].sort()
        if len(self.ods[instance_name].entries) == starting_number:
            logger.info("retaining all.")
            return
        self.ods[instance_name].gen_info()
        logger.info(f"retaining {self.ods[instance_name].number_of_records} of {starting_number}")


    ##############################################ADD############################################
    # Methods that add to the existing self.ods

    def add_new_record(self, instance_name=None, **kwargs):
        """
        Append a new record to self.ods.

        """
        instance_name = self.get_instance_name(instance_name)
        self.ods[instance_name].new_record(kwargs, defaults=self.defaults)
        self.ods[instance_name].gen_info()
        self.instance_report(instance_name=instance_name)

    def add_from_namespace(self, ns, instance_name=None):
        """
        Appends a new ods record to self.ods supplied as a Namespace

        """
        self.add_new_record(instance_name=instance_name, **vars(ns))

    def merge(self, from_ods, to_ods=ods_instance.DEFAULT_WORKING_INSTANCE, remove_duplicates=True):
        """
        Merge two ODS instances.

        Parameters
        ----------
        from_ods : str
            Name of ODS instance entries to be merged
        to_ods : str
            Name of ODS instance to be the merged ODS
        remove_duplicates : bool
            Flag to purge merged ODS of duplicates

        """
        logger.info(f"Updating {to_ods} from {from_ods}")
        self.add_from_list(self.ods[from_ods].entries, instance_name=to_ods, remove_duplicates=remove_duplicates)

    def add_from_list(self, entries, instance_name=None, remove_duplicates=True):
        """
        Append a records to self.ods[instance_name], using defaults then entries.
        
        Parameters
        ----------
        entries : list of dicts
            List of dictionaries containing ODS fields

        """
        instance_name = self.get_instance_name(instance_name)
        for entry in entries:
            self.ods[instance_name].new_record(entry, defaults=self.defaults)
        logger.info(f"Read {len(entries)} records from list.")
        if remove_duplicates:
            self.cull_by_duplicate(instance_name=instance_name)
        self.ods[instance_name].gen_info()
        self.instance_report(instance_name=instance_name)

    def add_from_file(self, data_file_name, instance_name=None, sep='auto', replace_char=None, header_map=None, remove_duplicates=True):
        """
        Append new records from a data file to self.ods; assumes the first line is a header.

        Parameters
        ----------
        data_file_name : str
            Name of input data file.
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
            - dict: {<ods_header_name>: <datafile_header_name>}

        """
        instance_name = self.get_instance_name(instance_name)
        self.data_file_name = data_file_name
        obs_list = tools.read_data_file(self.data_file_name, sep=sep, replace_char=replace_char, header_map=header_map)
        for _, row in obs_list.iterrows():
            self.ods[instance_name].new_record(row.to_dict(), defaults=self.defaults)
        logger.info(f"Read {len(obs_list.index)} records from {self.data_file_name}.")
        if remove_duplicates:
            self.cull_by_duplicate(instance_name=instance_name)
        self.ods[instance_name].gen_info()
        self.instance_report(instance_name=instance_name)

    ######################################OUTPUT##################################
    # Methods that show/save ods instance

    def view_ods(self, order=['src_id', 'src_start_utc', 'src_end_utc'], number_per_block=5, instance_name=None):
        """
        View the ods as a table arranged in blocks.

        Parameters
        ----------
        order : list
            First entries in table, rest of ods record values are append afterwards.
        number_per_block : int
            Number of records to view per block

        """
        instance_name = self.get_instance_name(instance_name)
        if not self.ods[instance_name].number_of_records:
            logger.info("No records to print.")
            return
        print(self.ods[instance_name].view(order=order, number_per_block=number_per_block))
    
    def graph_ods(self, numpoints=160, instance_name=None):
        """
        Text-based graph of ods times/targets.

        """
        instance_name = self.get_instance_name(instance_name)
        if not self.ods[instance_name].number_of_records:
            logger.info("No records to graph.")
            return
        self.ods[instance_name].graph(numpoints=numpoints)

    def plot_ods_coverage(self, instance_name=None, log=False):
        import matplotlib.pyplot as plt

        instance_name = self.get_instance_name(instance_name)
        self.cov_Tot, self.cov_times = self.check.coverage(self.ods[instance_name])
        for xx, yy in self.cov_times:
            plt.plot([xx, yy], [0, 0], lw=5)
        if log:
            self.check.read_log_file(log)
            from numpy import zeros
            ticks = zeros(len(self.check.log_data.keys()))
            plt.plot(self.check.log_data.keys(), ticks, 'k|', markersize=15)

    def write_file(self, file_name, instance_name=None, sep=','):
        """
        Export the ods to a data file.

        Parameters
        ----------
        file_name : str
            Name of data file
        instance_name : str or None
            ODS instance
        sep : str
            Separator to use

        """
        instance_name = self.get_instance_name(instance_name)
        if not self.ods[instance_name].number_of_records:
            logger.warning("Writing an empty ODS file!")
        self.ods[instance_name].export2file(file_name, sep=sep)