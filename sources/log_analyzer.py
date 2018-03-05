#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__: 'balychkov'

import os
import tempfile
import argparse
import logging
import json
import datetime

from nginx_log_analyzer import NginxLogAnalyzer

default_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    'TS_DIR': tempfile.gettempdir(),
    'LOGGING_DIR': None,
    'MAX_PARSE_ERRORS': 0.6
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='usage config file', default=None)
    args = parser.parse_args()

    cfg = dict(default_config)

    if args.config:
        with open(args.config, 'r') as f:
            cfg.update(json.load(f))

    # todo: смени level на INFO
    logging.basicConfig(filename=os.path.join(cfg['LOGGING_DIR'],
        __file__.replace('.py', '.log')) if cfg['LOGGING_DIR'] else None, level=logging.DEBUG,
        format='%(asctime)s %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    logging.info('START')

    try:
        inst = NginxLogAnalyzer(cfg['REPORT_DIR'], cfg['LOG_DIR'], cfg['REPORT_SIZE'], cfg['MAX_PARSE_ERRORS'])
        inst.create_report()

        with open(os.path.join(cfg['TS_DIR'], 'log_nalyzer.ts'), 'w') as f:
            f.write(str(datetime.datetime.now().timestamp()))
    except:
        logging.exception('Ошибка!')

    logging.info('DONE')


if __name__ == "__main__":
    main()
