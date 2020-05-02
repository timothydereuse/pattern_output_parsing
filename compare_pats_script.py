import json
import numpy as np
from collections import Counter
import itertools as it
from fractions import Fraction
from music21 import *
import os
import csv
import json

from load_pat_json import Pattern, load_patterns

morph_dict = {
    'C': 0,
    'D': 1,
    'E': 2,
    'F': 3,
    'G': 4,
    'A': 5,
    'B': 6,
}
degree_to_letter = {v: k for k, v in morph_dict.items()}

xmls = []
for root, dirs, files in os.walk(r"D:\Documents\felix_quartets_got_annotated"):
    for f in files:
        if f[-8:] == 'musicxml':
            xmls.append(os.path.join(root, f))

# fpath = xmls[66]
# xml = converter.parse(fpath)
# f_key = fpath.split('\\')[-1].split('.')[0]
# pats = load_patterns(rf'./patterns_output/{f_key}_patterns.json')
#
# measures = list(xml.parts[0].getElementsByClass(stream.Measure))


def get_prev_measure(measures, off):
    recent_measure = [x for x in measures if x.offset <= off][-1]
    measure_number = recent_measure.measureNumber
    beats = off - recent_measure.offset

    return (int(measure_number), beats)


for fpath in xmls:


    xml = converter.parse(fpath)
    f_key = fpath.split('\\')[-1].split('.')[0]
    measures = list(xml.parts[0].getElementsByClass(stream.Measure))

    in_pats = load_patterns(rf'./patterns_output/{f_key}_patterns.json')
    out_pats = []

    print(f'procesing {f_key}...')

    for p in in_pats:
        occs = []
        for r in p.regions:
            occ = {}
            occ['voice'] = int(r[0][0] // 10000)
            r[:, 0] %= 10000
            conc = np.array([get_prev_measure(measures, x) for x in r[:, 0]])
            conc = np.concatenate([conc, np.expand_dims(r[:, 1].astype(int), 1)], 1)
            # occ['onsets'] = conc.tolist()
            occ['end_measure_and_offset'] = (conc[-1][0], conc[-1][1])
            occ['num_onsets'] = len(conc)
            occ['start_measure_and_offset'] = (conc[0][0], conc[0][1])
            occ['note_name_sequence'] = ''.join([degree_to_letter[int(x % 7)] for x in conc[:, 2]])
            occs.append(occ)
        pat = {}
        pat['occurrences'] = occs

        if len(occs) < 2:
            continue

        pat['num_occurrences'] = len(occs)
        pat['median_cardinality'] = np.median([x['num_onsets'] for x in occs])
        out_pats.append(pat)

    with open(f'./patterns_output_cleaned/{f_key}_patterns_output.json', 'w') as fp:
        json.dump(out_pats, fp, indent=4)
