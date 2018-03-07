# -*- coding: utf-8 -*-

import unittest
import os
import subprocess

class AnalyzerTestCase(unittest.TestCase):

    def test_run_report(self):
        if os.path.exists('report-2017.01.01.html'):
            os.unlink('report-2017.01.01.html')

        res = subprocess.call(args=('python', '../sources/log_analyzer.py', '--config', 'config.json'))
        self.assertTrue(res == 0 and os.path.exists('report-2017.01.01.html'))


if __name__ == '__main__':
    unittest.main()
