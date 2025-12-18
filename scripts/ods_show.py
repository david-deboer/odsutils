#! /usr/bin/env python
import argparse
from odsutils import ods_engine

ap = argparse.ArgumentParser()
ap.add_argument('inputs', help='Inputs to show', nargs='?', default=None)
ap.add_argument('-s', '--sys', help='Show available system defaults files', action='store_true')
args = ap.parse_args()

if args.inputs is None:
    from odsutils import DATA_PATH
    from glob import glob
    defaults_files = glob(f"{DATA_PATH}/*.json")
    print("Available system defaults files:")
    for df in defaults_files:
        print('\t', df.split('/')[-1])
    print("To view, use name and -s flag.")
else:
    if args.sys:
        args.inputs = f"${args.inputs}"
    ods = ods_engine.ODS(version='latest', defaults=args.inputs)
    if args.inputs[0] != '$':
        ods.add(args.inputs)
    else:
        ods.add(site_id = ods.defaults.get('site_id', ''))
    print(f"ODS entries from {args.inputs}:")
    ods.view_ods()
    active = ods.check_active('now', read_from=args.inputs)
    print(f"Is active: {active}")