#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gzip
import argparse
import logging
import json
import tempfile
import datetime

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

default_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    'TS_DIR': tempfile.gettempdir(),
    'LOGGING': False
}

def create_report(rep_dir, log_dir, rep_sz):
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='usage config file', default=None)
    args = parser.parse_args()

    cfg = dict(default_config)

    if args.config:
        with open(args.config, 'r') as f:
            cfg.update(json.load(f))

    logging.basicConfig(filename=__file__.replace('.py', '.log') if cfg['LOGGING'] else None,
        level=logging.INFO, format='%(asctime)s %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    logging.info('START')

    create_report(cfg['REPORT_DIR'], cfg['LOG_DIR'], cfg['REPORT_SIZE'])

    with open(os.path.join(cfg['TS_DIR'], 'log_nalyzer.ts'), 'w') as f:
        f.write(datetime.datetime.now().timestamp())

    logging.info('DONE')


if __name__ == "__main__":
    main()
