# Operational Data Sharing (ODS)

This reads, writes, updates and checks ODS records.

Operational Data Sharing (ODS) is a protocol developed by NRAO in order to facilitate coexistance with the operation of satellite constellations, developed initially with conjuction with SpaceX with their Starlink satellite network. Ref.  This {\em ODSutils} codebase provides some utilities in order to implement and use it.  This codebase is meant to be stand-alone and so has a number of utilities for it and some other associated codebases.  The code may be installed by typing 'pip install https://github.com/david-deboer/odsutils'

The ``standard'' itself is defined is the {\tt ods\_standard.py} module.  The ODS standard is still under development and will evolve and different versions may be implemented there.

An \underline{ODS file} is a json file with one top key {\tt ods\_data} containing a list of dictionaries with the parameters.  An \underline{ODS instance} is a list of one of these parameter sets and is handled in in the {\tt ods\_instance.py} module.  "Instances" are lists of ODS records, and sometimes it is helpful to have multiple in play. ODS instance(s) can be handled in the {\tt ods\_engine.py} module.  The other file in the package are tool/utility modules.



There are currently two scripts
\begin{itemize}
    \item {\tt odsuser.py}:  has options allowing access to various {\tt ods\_engine.py} methods.
    \item {\tt ods\_online\_monitor.py}: grabs and saves a summary of active ODS records
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