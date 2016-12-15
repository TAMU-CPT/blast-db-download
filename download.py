#!/usr/bin/env python
import os
import sys
import time
import glob
import datetime
import random
import logging
import subprocess

try:  # py3
    from shlex import quote
except ImportError:  # py2
    from pipes import quote

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('dl')
NOW = datetime.datetime.now()
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATESTAMP = NOW.strftime("%Y-%V")
DATABASES = ('uniref50', 'uniref90', 'uniref100', 'nr', 'nt', 'representative')



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
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors="", time=time)

    def error(self, classname, test_name, errorMessage, errorDetails="", time=0):
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors=self.ERROR_TPL.format(
            errorMessage=errorMessage, errorDetails=errorDetails, test_name=test_name), time=time)

    def failure(self, classname, test_name, errorMessage, errorDetails="", time=0):
        self.xunit_data['total'] += 1
        self.__add_test(test_name, classname, errors=self.ERROR_TPL.format(
            errorMessage=errorMessage, errorDetails=errorDetails, test_name=test_name), time=time)

    def skip(self, classname, test_name, time=0):
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


xunit = XUnitReportBuilder('db_downloader')

for db in DATABASES:
    subprocess.check_call([
        'mkdir', '-p',
        os.path.join(db, DATESTAMP)
    ])

def timedCommand(classname, testname, errormessage, test_file, command, shell=False, cwd=None):
    if os.path.exists(test_file):
        xunit.skip(classname, testname)
    else:
        try:
            if not cwd:
                cwd = SCRIPT_DIR
            with Timer() as t:
                # If it's a shell command we automatically join things
                # to make our timedCommand calls completely uniform
                log.info(' '.join(command))
                if shell:
                    command = ' '.join(command)

                subprocess.check_call(command, shell=shell, cwd=cwd)
        except subprocess.CalledProcessError as cpe:
            xunit.failure(classname, testname, errormessage, errorDetails=str(cpe), time=t.interval)
        finally:
            xunit.ok(classname, testname, time=t.interval)


def uniref(db):
    d = os.path.join(db, DATESTAMP)
    fasta_file = os.path.join(d, db) + '.fa'
    pal_file = os.path.join(d, db) + '.pal'
    classname = 'blast.uniref.%s' % db

    # Download .fa
    timedCommand(classname, 'download', 'Download failed', fasta_file, [
        'curl',
        '--silent',
        'ftp://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/{db}/{db}.fasta.gz'.format(db=db),
        '|',
        'gzip -d',
        '>',
        fasta_file
    ])

    # Makeblastdb
    timedCommand(classname, 'build', 'Makeblastdb failed', pal_file, [
        'makeblastdb',
        '-in', fasta_file,
        '-dbtype', 'prot',
        '-out', os.path.join(d, db)
    ])


def ncbi():
    timedCommand('ncbi.index', 'download', 'Download failed', 'ncbi_index', [
        'curl',
        '--silent',
        'ftp://ftp.ncbi.nih.gov/blast/db/',
        '-o',
        'ncbi_index'
    ])

    nt_dir = os.path.join('nt', DATESTAMP)
    nt_urls = os.path.join(nt_dir, 'nt.urls')
    nr_dir = os.path.join('nr', DATESTAMP)
    nr_urls = os.path.join(nr_dir, 'nr.urls')

    timedCommand('ncbi.nt', 'urls', 'Download and Parsing Failed', nt_urls, [
        'cat', 'ncbi_index',
        '|',
        'grep', '-o', quote(' nt\..*gz'),
        '|',
        'sed', quote('s| |ftp://ftp.ncbi.nih.gov/blast/db/|g'),
        '>',
        nt_urls
    ], shell=True)

    timedCommand('ncbi.nt', 'download', 'Tarball Download Failed', os.path.join(nt_dir, 'nt.00.tar.gz'), [
        'wget',
        '--no-clobber',
        '--continue',
        '--input-file=nt.urls',
    ], cwd=nt_dir)

    for tarball in sorted(glob.glob(os.path.join(nt_dir, '*.tar.gz'))):
        basename = os.path.basename(tarball)
        shouldExist = tarball.replace('.tar.gz', '.nin')
        timedCommand('ncbi.nt', 'tar.extract.%s' % basename, 'Extraction failed', shouldExist, [
            'tar',
            '-xvf',
            basename
        ], cwd=nt_dir)


    timedCommand('ncbi.nr', 'urls', 'Download failed', nr_urls, [
        'cat', 'ncbi_index',
        '|',
        'grep', '-o', quote(' nr\..*gz'),
        '|',
        'sed', quote('s| |ftp://ftp.ncbi.nih.gov/blast/db/|g'),
        '>',
        nr_urls
    ], shell=True)

    timedCommand('ncbi.nr', 'download', 'Tarball Download Failed', os.path.join(nr_dir, 'nr.00.tar.gz'), [
        'wget',
        '--no-clobber',
        '--continue',
        '--input-file=nr.urls',
    ], cwd=nr_dir)

    for tarball in sorted(glob.glob(os.path.join(nr_dir, '*.tar.gz'))):
        basename = os.path.basename(tarball)
        shouldExist = tarball.replace('.tar.gz', '.pin')
        timedCommand('ncbi.nr', 'tar.extract.%s' % basename, 'Extraction failed', shouldExist, [
            'tar',
            '-xvf',
            basename
        ], cwd=nr_dir)


def representative():
    rep_dir = os.path.join('representative', DATESTAMP)
    urls_tsv = os.path.join(rep_dir, 'urls.tsv')
    classname = 'ncbi.representative_bacteria'
    timedCommand(classname, 'urls.tsv', 'Download URLs', urls_tsv, [
        'wget',
        quote('http://www.ncbi.nlm.nih.gov/genomes/Genome2BE/genome2srv.cgi?action=refgenomes&download=on&type=reference'),
        '-O',
        urls_tsv
    ], shell=True)

    gis_list = os.path.join(rep_dir, 'gis.list')
    timedCommand(classname, 'gis.list', 'Generate GI List', gis_list, [
        'awk', '-F"\\t"', '\'(NR>1){print $4}\'',
        '<', urls_tsv,
        '|',
        'sed', '"s/,/\\n/g"',
        '|',
        'sort', '-u',
        '>',
        gis_list
    ], shell=True)

    efetch_urls = os.path.join(rep_dir, 'efetch.urls')
    timedCommand(classname, 'efetch.urls', 'Generate EFetch URLs', efetch_urls, [
        'sed', quote('s|^|https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore\&rettype=gbwithparts\&retmode=text\&id=|g'),
        '<', gis_list,
        '>', efetch_urls
    ], shell=True)

    merged_fa = os.path.join(rep_dir, 'merged.fa')

    tmpfile = subprocess.check_output(['mktemp']).strip()

    if not os.path.exists(merged_fa):
        with open(efetch_urls, 'r') as handle:
            for line in handle:
                # URL from file
                url = line.strip()
                # Get genome ID: This could remove the step above but ...meh
                gid = url[url.rindex('=') + 1:]

                # IF ONLY THEY PROVIDED AN E-TAG WE WOULDN'T HAVE TO FRIGGING DO THIS.
                timedCommand(classname, 'wget.' + gid , 'Download ' + gid, 'does_not_exist', [
                    'curl',
                    '--silent',
                    '"%s"' % url,
                    '>>',
                    tmpfile
                ], shell=True)

                # Sleep to not piss NCBI off since they're touchy about this stuff. Grumbles.
                time.sleep(random.randint(1, 20))

    timedCommand(classname, 'protein_export', 'Export CDS Features', merged_fa, [
        'python',
        'feature_export.py',
        '--strip_stops',
        '--informative',
        '--translate',
        '--translation_table_id', '11',
        tmpfile, 'CDS',
        '>', merged_fa
    ], shell=True)

    timedCommand(classname, 'makeblastdb', 'Build BLAST Database', os.path.join(rep_dir, 'representative.pin'), [
        'makeblastdb',
        '-in', merged_fa,
        '-dbtype', 'prot',
        '-out', os.path.join(rep_dir, 'representative')
    ])
    subprocess.check_call(['rm', '-f', tmpfile])


if __name__ == '__main__':
    uniref('uniref50')
    uniref('uniref90')
    uniref('uniref100')
    ncbi()
    representative()

    # Write out the report
    with open(sys.argv[1], 'w') as handle:
        handle.write(xunit.serialize())
