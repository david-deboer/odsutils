#! /usr/bin/env python
import argparse
from odsutils import ods_engine

ap = argparse.ArgumentParser()
ap.add_argument('inputs', help='Inputs to show', nargs='?', default=None)
ap.add_argument('-s', '--sys', help='Show available system defaults files', action='store_true')
ap.add_argument('--defaults', help='Show default values', action='store_true')
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
    print(args.defaults)
    for k, v in ods.defaults.items():
        print(f"\t{k}: {v}")