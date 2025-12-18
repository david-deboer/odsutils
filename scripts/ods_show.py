#! /usr/bin/env python
import argparse
from odsutils import ods_engine

ap = argparse.ArgumentParser()
ap.add_argument('inputs', help='Inputs to show', nargs='?', default=None)
args = ap.parse_args()


if args.inputs is None:
    from odsutils import DATA_PATH
    from glob import glob
    defaults_files = glob(f"{DATA_PATH}/*.json")
    print("Available system defaults files:")
    for df in defaults_files:
        print('\t', df.split('/')[-1])
    print("To view, use name but prepend a '$' and don't forget to escape it.")
else:
    ods = ods_engine.ODS(version='latest', defaults=args.inputs)
    if args.inputs[0] == '$':
        ods.new_record()
    else:
        ods.add(args.inputs)

    print(f"ODS entries from {args.inputs}:")
    ods.view_ods()
    active = ods.check_active()
    print(f"Is active: {active}")