#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'balychkov'

import os
import tempfile
import argparse
import logging
import json
import datetime, time
import traceback

from nginx_log_analyzer import NginxLogAnalyzer

default_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    'TS_DIR': tempfile.gettempdir(),
    'LOGGING_DIR': None,
    'MAX_PARSE_ERRORS': 0.6
}

def prepare():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='usage config file', default=None)
    args = parser.parse_args()

    cfg = dict(default_config)
    cfg_load_error = None

    if args.config:
        try:
            with open(args.config, 'r') as f:
                cfg.update(json.load(f))
        except:
            cfg_load_error = traceback.format_exc()

    logging.basicConfig(filename=os.path.join(cfg['LOGGING_DIR'],
        os.path.split(__file__)[1].replace('.py', '.log')) if cfg['LOGGING_DIR'] else None, level=logging.INFO,
        format='%(asctime)s %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    if cfg_load_error:
        raise Exception('Не удалось загрузить переданный конфиг!\n{0}'.format(cfg_load_error))

    return cfg

def main():
    try:
        cfg = prepare()
        logging.info('START')
        inst = NginxLogAnalyzer(cfg['REPORT_DIR'], cfg['LOG_DIR'], cfg['REPORT_SIZE'], cfg['MAX_PARSE_ERRORS'])
        inst.create_report()

        with open(os.path.join(cfg['TS_DIR'], 'log_nalyzer.ts'), 'w') as f:
            f.write(str(time.mktime(datetime.datetime.now().timetuple())))
    except:
        logging.exception('Ошибка!')

    logging.info('DONE')
    logging.info('---------------------------------------------------------------------------------------------\n')


if __name__ == "__main__":
    main()
