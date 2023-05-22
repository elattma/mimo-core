from argparse import ArgumentParser
from datetime import datetime
from typing import Generator

from lake.s3 import S3Lake

_lake: S3Lake = None
_arg_parser: ArgumentParser = ArgumentParser()
_arg_parser.add_argument('--user', type=str, required=True)
_arg_parser.add_argument('--connection', type=str, required=True)
_arg_parser.add_argument('--integration', type=str, required=True)
_arg_parser.add_argument('--access_token', type=str, required=True)
_arg_parser.add_argument('--last_ingested_at', type=int, required=True)
_arg_parser.add_argument('--limit', type=int, default=100)

def main():
    global _lake
    
    print('hi!')

if __name__ == '__main__':
    main()