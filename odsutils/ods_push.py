import logging
import os
import re
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# ATA constants, filled into every field a record does not set itself.
ATA_DEFAULTS = {
    # Band to protect from satellite transmission
    # freq_actual_hz, supplied per observation.
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
    "subarray": 0,
}


def _tag(text):
    """Filename-safe version of text, or '' if nothing survives."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(text or "")).strip("._-")


def push_ods(
    src_id,
    ra_deg,
    dec_deg,
    freq_hz,
    *,
    project,
    length_hours,
    start=None,
    defaults=ATA_DEFAULTS,
    project_dir="/opt/mnt/share/ods_project",
    upload="/opt/mnt/share/ods_upload/ods.json",
):
    """
    Publish one reservation to the ODS feed.

    Writes a per-project file into project_dir and assembles the shared upload
    file. Site constants, including the avoidance band, come from defaults and
    fill every field not set here. Returns True on success, False otherwise,
    and never raises, so an ODS problem cannot stop an observation.

    Parameters
    ----------
    src_id : str
        Source name, also used in the per-project filename.
    ra_deg, dec_deg : float
        J2000 position in degrees.
    freq_hz : list of dicts
        Bands actually being received, one per tuning, stored in the record
        as given, e.g.
        [{"freq_lower_hz": 1000e6, "freq_upper_hz": 1672e6},
         {"freq_lower_hz": 4200e6, "freq_upper_hz": 4872e6}].
        Pass [] to publish without the field, e.g. when the tunings cannot
        be read.
    project : str
        Short project tag keeping this project's file distinct from others'.
    length_hours : float
        Reservation duration.
    start : datetime or None
        Reservation start; None means now. Naive datetimes are treated as UTC.
    defaults : dict
        Site constants merged under the record's own fields; ATA's by default.
    project_dir : str
        Directory the per-project ODS files are written into.
    upload : str
        Filename the assembled ODS is posted to.

    """
    from . import ods_engine

    src = _tag(src_id)
    proj = _tag(project)
    if not src or not proj:
        logger.error(
            f"ODS push failed: src_id {src_id!r} / project {project!r} "
            "have no filename-safe characters"
        )
        return False
    try:
        ra_deg, dec_deg = float(ra_deg), float(dec_deg)
    except (TypeError, ValueError):
        logger.error(f"ODS push failed: ra/dec not numeric: {ra_deg!r}, {dec_deg!r}")
        return False
    try:
        bands = [
            {"freq_lower_hz": float(b["freq_lower_hz"]),
             "freq_upper_hz": float(b["freq_upper_hz"])}
            for b in freq_hz
        ]
    except (KeyError, TypeError, ValueError):
        logger.error("ODS push failed: freq_hz must be one dict per tuning, e.g. "
                     '[{"freq_lower_hz": 1000e6, "freq_upper_hz": 1672e6}]; '
                     f"got {freq_hz!r}")
        return False
    if any(b["freq_upper_hz"] <= b["freq_lower_hz"] for b in bands):
        logger.error(f"ODS push failed: freq_upper_hz <= freq_lower_hz: {bands!r}")
        return False

    if start is None:
        start = datetime.now(timezone.utc)
    elif not isinstance(start, datetime):
        logger.error(f"ODS push failed: start must be a datetime, got {start!r}")
        return False
    elif start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(hours=float(length_hours))
    if end <= start:
        logger.error(
            f"ODS push failed: length_hours must be positive, got {length_hours!r}"
        )
        return False

    cfg = dict(defaults)
    cfg.update(
        {
            "src_id": src,
            "src_ra_j2000_deg": ra_deg,
            "src_dec_j2000_deg": dec_deg,
            "src_start_utc": start.astimezone(timezone.utc)
            .replace(tzinfo=None)
            .isoformat(timespec="seconds"),
            "src_end_utc": end.astimezone(timezone.utc)
            .replace(tzinfo=None)
            .isoformat(timespec="seconds"),
        }
    )
    if bands:
        cfg["freq_actual_hz"] = bands

    try:
        os.makedirs(project_dir, exist_ok=True)
        upload_dir = os.path.dirname(upload)
        if upload_dir:
            os.makedirs(upload_dir, exist_ok=True)

        ods = ods_engine.ODS(conlog="ERROR")
        ods.add(cfg)
        ods.update_by_elevation()
        ods.post_ods(os.path.join(project_dir, f"ods_{proj}_{src}.json"))
        ods.assemble_ods(project_dir, post_to=upload)
    except Exception as e:
        logger.error(f"ODS push failed for {src}: {e}")
        return False
    logger.info(f"ODS push succeeded for {src}")
    return True
