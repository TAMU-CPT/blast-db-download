#!/usr/bin/env python
import os
import sys
import glob

START_TAG = '## START AUTOGENERATED. DO NOT MODIFY MANUALLY ##'
END_TAG = '## END AUTOGENERATED ##'


SPECIAL_SNOWFLAKES = {
    'nt': {
        "2014-08": ['nt_aug2014', 'NT August 2014'],
        "2015-09": ['nt_aug2015', 'NT August 2015'],
        "2016-09": ['nt_aug2016', 'NT August 2016'],
    },
    'nr': {
        "2014-08": ['nr_aug2014', 'NR August 2014'],
        "2015-08": ['nr_aug2015', 'NR August 2015'],
        "2016-09": ['nr_aug2016', 'NR August 2016'],
    },
    'bact': {
        "2016-08": ['bact_aug2016', 'NCBI Bacteria August 2016'],
    },
    'phage': {
        '2016-08': ['canonical_phages_1', 'Canonical Phages August 2016'],
    },
    'representative': {
        '2016-09': ['representative', 'Representative Bacteria August 2016'],
    },
    'uniref100': {
        '2016-08': ['uniref100_aug2016', 'Uniref100 August 2016'],
    },
    'uniref50': {
        '2016-01': ['uniref50_jan2016', 'Uniref50 January 2016'],
        '2016-08': ['uniref50_aug2016', 'Uniref50 August 2016'],
    },
    'uniref90': {
        '2016-01': ['uniref90_jan2016', 'Uniref90 January 2016'],
        '2016-08': ['uniref90_aug2016', 'Uniref90 August 2016'],
    }
}


PROT_DBS = [
    'nr', 'uniref50', 'uniref90', 'uniref100',
    # Custom names
    ['phage', 'canonical_phages', 'Canonical Phages'],
    ['representative', 'representative', 'NCBI Representative Bacteria'],
    ['bact', 'bact', 'NCBI All Bacteria'],
    ['sprot', 'sprot', 'Uniprot Swiss-Prot'],
    ['trembl', 'trembl', 'Uniprot TrEMBL'],
]

NUCL_DBS = [
    'nt'
]

PROT_LOC = []
NUCL_LOC = []

for db in PROT_DBS:
    if isinstance(db, list):
        dir_name, index_name, title = db
    else:
        dir_name = db
        index_name = db
        if db == 'nr':
            title = 'NR'
        else:
            title = db[0].upper() + db[1:]

    for date in sorted(glob.glob('%s/*' % dir_name))[::-1]:
        date = date.split('/')[1]
        if date in SPECIAL_SNOWFLAKES[dir_name]:
            year, month = date.split('-')
            key, title = SPECIAL_SNOWFLAKES[dir_name][date]
            PROT_LOC.append([
                key,
                '[Permanent] ' + title,
                '/media/nfs-backup/blast/%s/%s-%s/%s' % (dir_name, year, month, index_name)
            ])
        else:
            year, week = date.split('-')
            week = int(week)
            permanence = ''
            if week % 13 == 0:
                permanence = '[Permanent] '

            PROT_LOC.append([
                '%s_%s.%s' % (index_name, year, week),
                '%s%s %s-%s' % (permanence, title, year, week + 1),
                '/media/nfs-backup/blast/%s/%s-%02d/%s' % (dir_name, year, week, index_name)
            ])

for db in NUCL_DBS:
    if isinstance(db, list):
        dir_name, index_name, title = db
    else:
        dir_name = db
        index_name = db
        if db == 'nt':
            title = 'NT'
        else:
            title = db[0].upper() + db[1:]

    for date in sorted(glob.glob('%s/*' % dir_name))[::-1]:
        date = date.split('/')[1]
        if date in SPECIAL_SNOWFLAKES[dir_name]:
            year, month = date.split('-')
            key, title = SPECIAL_SNOWFLAKES[dir_name][date]
            NUCL_LOC.append([
                key,
                '[Permanent] ' + title,
                '/media/nfs-backup/blast/%s/%s-%s/%s' % (dir_name, year, month, index_name)
            ])
        else:
            year, week = date.split('-')
            week = int(week)
            permanence = ''
            if week % 13 == 0:
                permanence = '[Permanent] '
            NUCL_LOC.append([
                '%s_%s.%s' % (index_name, year, week),
                '%s%s %s-%s' % (permanence, title, year, week + 1),
                '/media/nfs-backup/blast/%s/%s-%02d/%s' % (dir_name, year, week, index_name)
            ])

NUCL_FILE = sys.argv[1]
PROT_FILE = sys.argv[2]

with open(NUCL_FILE, 'r+') as handle:
    data = handle.readlines()
    file_lines = []

    in_replacement = False
    for line in data:
        line = line.strip()
        if line == START_TAG:
            in_replacement = True
            # This will be our marker
            file_lines.append(None)
        elif line == END_TAG:
            in_replacement = False
        elif not in_replacement:
            file_lines.append(line)

    none_idx = file_lines.index(None)
    first_half = file_lines[0:none_idx]
    second_half = file_lines[none_idx+1:]

    new_file_lines = \
        first_half + [START_TAG] + \
        ['\t'.join(x) for x in NUCL_LOC]

    if 'BUILD_URL' in os.environ:
        new_file_lines += ['# Automated build: ' + os.environ['BUILD_URL']]

    new_file_lines += [END_TAG] + second_half
    handle.seek(0)
    handle.truncate()
    handle.write('\n'.join(new_file_lines))

with open(PROT_FILE, 'r+') as handle:
    data = handle.readlines()
    file_lines = []

    in_replacement = False
    for line in data:
        line = line.strip()
        if line == START_TAG:
            in_replacement = True
            # This will be our marker
            file_lines.append(None)
        elif line == END_TAG:
            in_replacement = False
        elif not in_replacement:
            file_lines.append(line)

    none_idx = file_lines.index(None)
    first_half = file_lines[0:none_idx]
    second_half = file_lines[none_idx+1:]

    new_file_lines = \
        first_half + [START_TAG] + \
        ['\t'.join(x) for x in PROT_LOC]

    if 'BUILD_URL' in os.environ:
        new_file_lines += ['# Automated build: ' + os.environ['BUILD_URL']]

    new_file_lines += [END_TAG] + second_half
    handle.seek(0)
    handle.truncate()
    handle.write('\n'.join(new_file_lines))

