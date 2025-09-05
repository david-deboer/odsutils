# Operational Data Sharing (ODS)

This reads, writes, updates and checks ODS records.

Operational Data Sharing (ODS) is a protocol developed by NRAO in order to facilitate coexistance with the operation of satellite constellations, developed initially with conjuction with SpaceX with their Starlink satellite network. Ref.  This {\em ODSutils} codebase provides some utilities in order to implement and use it.  This codebase is meant to be stand-alone and so has a number of utilities for it and some other associated codebases.  The code may be installed by typing 'pip install https://github.com/david-deboer/odsutils'

The ``standard'' itself is defined is the {\tt ods\_standard.py} module.  The ODS standard is still under development and will evolve and different versions may be implemented there.

An \underline{ODS file} is a json file with one top key {\tt ods\_data} containing a list of dictionaries with the parameters.  An \underline{ODS instance} is a list of one of these parameter sets and is handled in in the {\tt ods\_instance.py} module.  "Instances" are lists of ODS records, and sometimes it is helpful to have multiple in play. ODS instance(s) can be handled in the {\tt ods\_engine.py} module.  The other file in the package are tool/utility modules.

The pipeline is to import ODS into your code and then post the ODS record.  To handle multiple observers that need to generate an ODS there is the concept of "assembling" an overall ODS file.  To help, there are two methods used:  `post_to` and `assemble_ods`.

`post_to` just writes an ODS instance to a file
`assemble_ods` reads in all ODS files from a directory, assembles them and can then (optionally) post that.
The code snippet used is then
```
from odsutils import ods_engine
ods = ods_engine.ODS()
list_containing_dicts_with_ODS_values = [{'src_ra_j2000_deg': 123.0, 'src_dec_j2000_deg': -23.0, 'src_start_utc': '2025-09-28T11:25:45',
      'src_end_utc': '2025-09-28T14:25:45', ...}, ...]
ods.read_ods(list_containing_dicts_with_ODS_values)
ods.post_ods('/directory_for_holding_ODS_files/ods_someprojectname.json')
ods.assemble_ods('/directory_for_holding_ODS_files', post_to='/directory_for_uploading_file/ods.json')
```
Note that ods.read_ods() can also read in a file if you give it a filename, or pull a json from the web if given a URL.
`ods.assemble_ods` will cull old entries, as well as remove duplicates.

If you don't need to assemble, you can just post directly to '/directory_for_uploading_file/ods.json'.

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