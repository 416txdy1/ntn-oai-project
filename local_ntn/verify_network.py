"""Verify and manage the exact RuntimeConfig-owned RFsim topology."""
import argparse
import os
from pathlib import Path
from network_owner import NetworkManager
from runtime_config import resolve_runtime


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',default='')
    parser.add_argument('--run-id',default='')
    parser.add_argument('--claim',action='store_true')
    parser.add_argument('--action',choices=('verify','up','down'),default='verify')
    args=parser.parse_args(argv)
    if os.geteuid()!=0:parser.exit(1,'Network verification requires sudo\n')
    try:
        config=resolve_runtime(Path(__file__).resolve().parents[1],args.profile,args.run_id,os.environ)
        manager=NetworkManager(config)
        if args.action=='up':manager.up()
        elif args.action=='down':manager.down()
        else:manager.verify(args.claim)
    except (ValueError,OSError,KeyError) as error:parser.exit(1,f'Network refused: {error}\n')
    print(f'Verified owned {config.namespace} topology ({args.action})')

if __name__=='__main__':main()
