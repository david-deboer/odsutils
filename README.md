# Operational Data Sharing (ODS)

This reads, writes, updates and checks ODS records.

Operational Data Sharing (ODS) is a protocol developed by NRAO in order to facilitate coexistance with the operation of satellite constellations, developed initially with conjuction with SpaceX with their Starlink satellite network to facilitate telescope boresight avoidance. Ref.  This `ODSutils` codebase provides some utilities in order to implement and use it.  This codebase is meant to be stand-alone and so has a number of utilities for it and some other associated codebases.  The code may be installed by typing `pip install https://github.com/david-deboer/odsutils`.

The standard itself is defined is the `ods_standard.py` module (see NRAO website).  The ODS standard is still under development and will evolve and different versions may be implemented there.  There are currently two standards, denoted "A" and "B".  "A" is deprecated.

An **ODS file** is a json file with one top key (`ods_data`) containing a list of key-value pairs with the parameters (so effectively a list of dictionaries).  Each element in this list is an **ods_record**.

An **ODS instance** is a list of ods_records per above and is handled in the `ods_instance.py` module.  "Instances" are named lists of ODS records, and sometimes it is helpful to have multiple in play.  For example, when a new composite ODS file is assembled, multiple instances are created and merged.

ODS instance(s) can be handled in the **ods_engine.py** module, which is generally the only one invoked.

The general pipeline is as follows:

1. Create an ODS file with the data for your observation (see below)
2. Post the ODS file (the convention is ods*.json, where * is a descriptor):
  -  If this observation is the only ODS information to handle, post it directly for satellite company and you are done.
  -  If this observation is one of potentially many, post it to a "holding" directory for "assembly".
3. If you are assembling and posting, run the assembly method.  That method will remove old and duplicate ods_records.

The code snippet below is for the just posting case:

```
from odsutils import ods_engine
ods = ods_engine.ODS(defaults='ods_defaults.json')
...see create an ODS file below
ods.post_ods('directory_for_uploading_file/ods.json')
```

Note that the `defaults` keyword gives either the filename or a dictionary for the default ods instance values.  Without it you will need to set all parameters explicitly for a given standard.  There are some built-in defaults accessed by a '$'; e.g. `defaults = '$ods_defaults_ata_B.json'`.

This code snippet handles the pipeline for the full case:

```
from odsutils import ods_engine
ods = ods_engine.ODS(defaults='$ods_defaults_ata_B.json')
...see create an ODS file below
ods.post_ods('/directory_for_holding_ODS_files/ods_descriptor.json')
ods.assemble_ods('/directory_for_holding_ODS_files', post_to='/directory_for_uploading_file/ods.json')
```

# Create an ODS file
As mentioned above, an ODS file is a list of ODS records in the JSON format and everything is under one key called `ods_data`.  Each ODS record is an observation, but each record in an ODS file must have the complete set of ODS keys.

Note that in specifying an observation, you typically don't want to include all of the ODS keys, which is why there is a defaults file.  If one is specified, when a new ODS record is created, it populates it with the default values then includes the observation parameters, like RA/Dec, start time, stop time, source ID.  If a defaults file is not specified, one must make sure to include all of the ODS parameters when you make a record.

When you make an ods class instance via `ods = ods.ods_engine(...)` it creates a default ODS instance, which is probably all you need (that is, you don't have to worry about creating or handling multiple ODS instances) -- you just need to add ODS records to it.

The primary method to add records is `ods.add(...)`.  It takes a dictionary, a list of dictionaries or a filename.  As mentioned above, if a defaults input file is present, it will populate a record with the default information then include the new information.  One can also `ods.merge(...)` ODS records from another named instance.

The dictionary or list uses those key-value pairs as data for an ODS record.  If a string is provided, it assumes that it is a filename and it will read that file.  If the filename does not end with '.json', then you can specify a format for a csv file.

The code snippet below shows the simplest way to create an ODS file, assuming that there is a local file name `ods_defaults.json` which holds a complete set of ODS parameters.

```
from odsutils import ods_engine
ods = ods_engine.ODS()
ods.add([{"src_id": "Source1",
          "src_ra_j2000_deg": 130.86,
          "src_dec_j2000_deg": 18.15,
          "src_start_utc": "2025-09-28T11:25:45",
          "src_end_utc": "2025-09-28T14:25:45"},
         {"src_id": "Source2",
          "src_ra_j2000_deg": 92.74,
          "src_dec_j2000_deg": 22.25,
          "src_start_utc": "2025-09-28T14:45:30",
          "src_end_utc": "2025-09-28T15:25:45"},
         {"src_id": "Source3",
          "src_ra_j2000_deg": 265.87,
          "src_dec_j2000_deg": 45.94,
          "src_start_utc": "2025-09-28T15:55:00",
          "src_end_utc": "2025-09-28T16:30:10"}]) 
ods.post_ods('ods_myproj.json')
```

# Scripts

Additionally, there are three scripts

	odsuser.py:  has options allowing access to various {\tt ods\_engine.py} methods.
	ods\_online\_monitor.py: grabs and saves a summary of active ODS records from a URL
	ods\_show\_defaults.py: shows information in default files


ACKNOWLEDGEMENTS
This software was developed with support from the National Science Foundation:
SII-NRDZ: Radio Astronomy Dynamic Satellite Inteference-Mitigation and Spectrum Sharing (RADYSISS) (AST-2232368)

The ODS system was developed by NRAO with support from the National Science Foundation's grants:
SII NRDZ: Dynamic Protection and Spectrum Monitoring for Radio Observatories (AST-2232159),
SWIFT-SAT: Observational Data Sharing (AST-2332422)