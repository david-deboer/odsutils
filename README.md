# Operational Data Sharing (ODS)

This reads, writes, updates and checks ODS records.

Operational Data Sharing (ODS) is a protocol developed by NRAO in order to facilitate coexistance with the operation of satellite constellations, developed initially with conjuction with SpaceX with their Starlink satellite network to facilitate telescope boresight avoidance. Ref.  This `ODSutils` codebase provides some utilities in order to implement and use it.  This codebase is meant to be stand-alone and so has a number of utilities for it and some other associated codebases.  The code may be installed by typing `pip install https://github.com/david-deboer/odsutils`.

The standard itself is defined is the `ods_standard.py` module (see NRAO website).  The ODS standard is still under development and will evolve and different versions may be implemented there.  There are currently two standards, denoted "A" and "B".  "A" is deprecated.

An **ODS file** is a json file with one top key (`ods_data`) containing a list of dictionaries with the parameters.  Each element in this list is an **ods_record**.

An **ODS instance** is a list of ods_records and is handled in the `ods_instance.py` module.  "Instances" are lists of ODS records, and sometimes it is helpful to have multiple in play.  For example, when a new composite ODS file is assembled, multiple instances are created and merged.

ODS instance(s) can be handled in the **ods_engine.py** module.

The general pipeline is as follows:

1. Create an ODS file with the data for your observation (see below)
2. Post the ODS file (the convention is ods*.json, where the * is a descriptor):
  -  If this observation is the only ODS information to handle, post it directly for SpaceX and you are done.
  -  If this observation is one of potentially many, post it to a "holding" directory for "assembly".
3. If you assembling and posting, run the assembly method.  That method will remove old and duplicate ods_records.

The code snippet below is for the just posting case:

```
from odsutils import ods_engine
ods = ods_engine.ODS(conlog='WARNING', defaults='<default file name>')
...see create an ODS file below
ods.post_ods('directory_for_uploading_file/ods.json')
```

This code snippet handles the pipeline for the full case:

```
from odsutils import ods_engine
ods = ods_engine.ODS(conlog='WARNING', defaults='<default file name>')
...see create an ODS file below
ods.post_ods('/directory_for_holding_ODS_files/ods_descriptor.json')
ods.assemble_ods('/directory_for_holding_ODS_files', post_to='/directory_for_uploading_file/ods.json')
```

In the class instance call, `conlog='WARNING'` just sets the logging level and `default=<default file name>` sets a default file, as discussed below.  If no default file is given, None is used.

# Create an ODS file
As mentioned above, an ODS file is a list of ODS records (which is called an ODS instance).  It is in the JSON format and everything is under one key called `ods_data`.  Each ODS record is an observation, but each record must have the full number of ODS keys.

Note that in specifying an observation, you typically don't want to include all of the ODS keys, which is why there is a defaults file.  If one is specified, when a new ODS record is created, it populates it with the default values then includes the observation parameters, like RA/Dec, start time, stop time, source ID.  If a defaults file is not specified, one must make sure to include all of the ODS parameters when you make a record.

When you make an ods class instance via `ods = ods.ods_engine(...)` it creates a default ODS instance, which is probably all you need (that is, you don't have to worry about creating or handling multiple ODS instances) -- you just need to add ODS records to it.


Note that ods.read_ods() can also read in a file if you give it a filename, or pull a json from the web if given a URL.
`ods.assemble_ods` will cull old entries, as well as remove duplicates.

IT ASSUMES THAT ALL FIELDS ARE PRESENT AND OF THE CORRECT FORMAT.  OTHERWISE IT WILL IGNORE IT.


Additionally, there are two scripts
\begin{itemize}
    \item {\tt odsuser.py}:  has options allowing access to various {\tt ods\_engine.py} methods.
    \item {\tt ods\_online\_monitor.py}: grabs and saves a summary of active ODS records from a URL
\end{itemize}

Reading may come from an existing ODS file, from a datafile or be provided by a dictionary or Namespace.

Records read from a datafile or supplied, are appended to whatever ODS records are already contained in the class ODS list.
Reading an ODS file, will start a new/different class ODS list.

ODS lists may be updated/culled based on a few checks.

ODS checks are:
1. all supplied record entries have the right "name"
2. all entries are present and have the right type
3. sources above horizon (update_by_elevation)

Standard pip install.

The presumed workflow (as shown in odsuder.py and can be done in one call) is:
1. read in an existing ODS file
2. set the defaults you want (either a json file with default values or 'from_ods')
3. add entries from a data file or can add on command line
4. remove entries before a time (likely 'now')
5. write the new ods file (give same filename to overwrite)

E.g.

`odsuser.py -o ods_ata.json -d from_ods -f obs.txt -i -t now -w ods_new.json`

`odsuser.py -d sites.json:ata -f obs.txt -i -t now -w ods_new.json`

ACKNOWLEDGEMENTS
This software was developed with support from the National Science Foundation:
SII-NRDZ: Radio Astronomy Dynamic Satellite Inteference-Mitigation and Spectrum Sharing (RADYSISS) (AST-2232368)

The ODS system was developed by NRAO with support from the National Science Foundation's grants:
SII NRDZ: Dynamic Protection and Spectrum Monitoring for Radio Observatories (AST-2232159),
SWIFT-SAT: Observational Data Sharing (AST-2332422)