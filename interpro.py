#!/usr/bin/env python
import os
import sys
import time
import datetime
import logging
import subprocess


logging.basicConfig(level=logging.INFO)
log = logging.getLogger('dl')
NOW = datetime.datetime.now()
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DOWNLOAD_ROOT = os.getcwd()
VERSION = '5.22-61.0'


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start


class XUnitReportBuilder(object):
    XUNIT_TPL = """<?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="{suite_name}" tests="{total}" errors="{errors}" failures="{failures}" skip="{skips}">
{test_cases}
    </testsuite>
    """

    TESTCASE_TPL = """        <testcase classname="{classname}" name="{name}" {time}>
{error}
        </testcase>"""

    ERROR_TPL = """            <error type="{test_name}" message="{errorMessage}">{errorDetails}
            </error>"""

    def __init__(self, suite_name):
        self.xunit_data = {
            'total': 0, 'errors': 0, 'failures': 0, 'skips': 0
        }
        self.test_cases = []
        self.suite_name = suite_name

    def ok(self, classname, test_name, time=0):
        log.info("OK: [%s] %s", classname, test_name)
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors="", time=time)

    def error(self, classname, test_name, errorMessage, errorDetails="", time=0):
        log.info("ERROR: [%s] %s", classname, test_name)
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors=self.ERROR_TPL.format(
            errorMessage=errorMessage, errorDetails=errorDetails, test_name=test_name), time=time)

    def failure(self, classname, test_name, errorMessage, errorDetails="", time=0):
        log.info("FAIL: [%s] %s", classname, test_name)
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors=self.ERROR_TPL.format(
            errorMessage=errorMessage, errorDetails=errorDetails, test_name=test_name), time=time)

    def skip(self, classname, test_name, time=0):
        log.info("SKIP: [%s] %s", classname, test_name)
        self.xunit_data['skips'] += 1
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors="            <skipped />", time=time)

    def __add_test(self, name, classname, errors, time=0):
        t = 'time="%s"' % time
        self.test_cases.append(
            self.TESTCASE_TPL.format(name=name, error=errors, classname=classname, time=t))

    def serialize(self):
        self.xunit_data['test_cases'] = '\n'.join(self.test_cases)
        self.xunit_data['suite_name'] = self.suite_name
        return self.XUNIT_TPL.format(**self.xunit_data)


xunit = XUnitReportBuilder('interpro_installer')


def timedCommand(classname, testname, errormessage, test_file, command, shell=False, cwd=None):
    if os.path.exists(test_file):
        xunit.skip(classname, testname)
    else:
        try:
            if not cwd:
                cwd = DOWNLOAD_ROOT
            with Timer() as t:
                # If it's a shell command we automatically join things
                # to make our timedCommand calls completely uniform
                log.info('cd %s && ' % cwd + ' '.join(command))
                if shell:
                    command = ' '.join(command)

                subprocess.check_call(command, shell=shell, cwd=cwd)
            xunit.ok(classname, testname, time=t.interval)
        except subprocess.CalledProcessError as cpe:
            xunit.failure(classname, testname, errormessage, errorDetails=str(cpe), time=t.interval)


def interpro():
    classname = 'interpro'
    tarball = 'interproscan-%s-64-bit.tar.gz' % VERSION
    md5sum = tarball + '.md5'
    base_url = 'ftp://ftp.ebi.ac.uk/pub/software/unix/iprscan/5/%s/' % VERSION

    timedCommand(classname, 'download.tarball', 'Download failed', tarball, [
        'wget',
        base_url + tarball,
        '-O', tarball,
    ])

    timedCommand(classname, 'download.md5sum', 'Download failed', md5sum, [
        'wget',
        base_url + md5sum,
        '-O', md5sum,
    ])

    timedCommand(classname, 'contents.verify', 'MD5SUM failed to validate', 'none', [
        'md5sum', '-c', md5sum
    ])

    timedCommand(classname, 'contents.extract', 'Failed to extract', 'none', [
        'tar', 'xvfz', tarball
    ])

if __name__ == '__main__':
    interpro()

    # Write out the report
    with open(sys.argv[1], 'w') as handle:
        handle.write(xunit.serialize())
