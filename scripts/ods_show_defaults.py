#! /usr/bin/env python
import argparse
from odsutils import ods_engine

ap = argparse.ArgumentParser()
ap.add_argument('defaults', help='Defaults to query', nargs='?', default=None)
ap.add_argument('-s', '--sys', help='Show available system defaults files', action='store_true')
args = ap.parse_args()

if args.defaults is None:
    from odsutils import DATA_PATH
    from glob import glob
    defaults_files = glob(f"{DATA_PATH}/*.json")
    print("Available system defaults files:")
    for df in defaults_files:
        print('\t', df.split('/')[-1])
    print("To view use name and -s flag.")
else:
    if args.sys:
        args.defaults = f"${args.defaults}"
    ods = ods_engine.ODS(version='latest', defaults=args.defaults)
    print(args.defaults)
    for k, v in ods.defaults.items():
        print(f"\t{k}: {v}")