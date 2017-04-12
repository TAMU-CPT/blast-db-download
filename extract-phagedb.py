#!/usr/bin/env python
import sys
import json
from tqdm import tqdm
from Bio import SeqIO


data = []
for rec in tqdm(SeqIO.parse(sys.stdin, 'genbank')):
    data.append({
        'id': rec.id,
        'desc': rec.description,
        'name': rec.name,
        'source': rec.annotations.get('source', None)
    })

json.dump(data, sys.stdout, indent=2)
