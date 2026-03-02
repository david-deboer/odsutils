from os.path import join
from importlib.metadata import version
__version__ = version('odsutils')

try:
    import warnings
    from erfa import ErfaWarning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ErfaWarning)
except ImportError:
    pass

DATA_PATH = join(__path__[0], 'data')
LOG_FORMATS = {'conlog_format': "{asctime} - {levelname} - {module} - {message}",
               'filelog_format': "{asctime} - {levelname} - {module} - {message}"}
LOG_FILENAME = 'odslog'


SITES = {
    'testing': {
        'project': './test_proj.json',
        'upload': './test_upload.json',
        'url': '',
        'defaults': {
            "freq_lower_hz": 1990000000,
            "freq_upper_hz": 1995000000,
            "site_id": "ATA",
            "site_lat_deg": 40.817431,
            "site_lon_deg": -121.470736,
            "site_el_m": 1019.222,
            "trk_rate_ra_deg_per_sec": 0,
            "trk_rate_dec_deg_per_sec": 0,
            "slew_sec": 30,
            "corr_integ_time_sec": 1,
            "version": "v1.0.0",
            "dish_diameter_m": 6.1,
            "subarray": 0
        }
        },
    'ata': {
        'project': "/opt/mnt/share/ods_project/ods_rados.json",
        'upload': "/opt/mnt/share/ods_upload/ods.json",
        'url': "https://ods.hcro.org/ods.json",
        'defaults': {
            "freq_lower_hz": 1990000000,
            "freq_upper_hz": 1995000000,
            "site_id": "ATA",
            "site_lat_deg": 40.817431,
            "site_lon_deg": -121.470736,
            "site_el_m": 1019.222,
            "trk_rate_ra_deg_per_sec": 0,
            "trk_rate_dec_deg_per_sec": 0,
            "slew_sec": 30,
            "corr_integ_time_sec": 1,
            "version": "v1.0.0",
            "dish_diameter_m": 6.1,
            "subarray": 0
        }
        }
        }