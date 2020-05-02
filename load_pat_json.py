import json
import numpy as np
from collections import Counter
import itertools as it
from fractions import Fraction
import os
import csv

class Pattern(object):
    __slots__ = 'identifier', 'cardinality', 'span', 'regions', 'intervals'

    def __init__(self, regions, identifier='', cardinality=-1, span=-1):
        self.regions = regions
        self.cardinality = cardinality
        self.identifier = identifier
        self.span = span
        self.intervals = [
            (min(x[:,0]) % 10000, max(x[:,0]) % 10000, int(x[0][0] // 10000))
        for x in self.regions]


def load_patterns(fname):
    with open(fname) as f:
        pat_dict = json.load(f)

    for x in range(len(pat_dict) - 1, -1, -1):
        if type(pat_dict[x]['categoryMembers']) is dict:
            del pat_dict[x]

    pats = []
    for i, entry in enumerate(pat_dict):
        # c = Counter([int(m['pattern'][0][0] / 10000) for m in x['categoryMembers']])
        # print(f"i: {i}, cardinality: {x['cardinality']}, num_occs: {len(x['categoryMembers'])}, {c}")

        regions = []

        raw_regions = [np.array(x['region']).astype('float') for x in entry['categoryMembers']]
        # raw_regions += [np.array(x).astype('float') for x in entry['inexactOccurrences']['regions']]
        for r in raw_regions:
            if len(r) <= 2 or any([np.array_equal(r, x) for x in regions]):
                continue
            regions.append(r)

        pats.append(Pattern(regions, '', entry['cardinality'], entry['span']))
    return pats


def cardinality_score(A, B):
    # try:
    #     nrows, ncols = A.shape
    # except ValueError:
    #     ncols = A.shape[0]
    # dtype = {'names': ['f{}'.format(i) for i in range(ncols)],
    #          'formats': ncols * [A.dtype]}
    temp_dtype = {'names': ['f0', 'f1'], 'formats': [np.dtype('float64'), np.dtype('float64')]}

    # if there is no time overlap, don't even bother:
    a_start, a_end = min(A[:, 0]), max(A[:, 0])
    b_start, b_end = min(B[:, 0]), max(B[:, 0])
    if not (a_start < b_end) and (b_start < a_end):
        return 0

    translations = set()
    for x, y in it.product(range(A.shape[0]), range(B.shape[0])):
        translations.add(tuple(B[y] - A[x]))

    amts = []
    for t in translations:
        c = np.intersect1d((A + t).view(temp_dtype), B.view(temp_dtype))
        amts.append(c.shape[0])

    div = max(A.shape[0], B.shape[0])
    int_amt = max(amts)
    return int_amt / div


def score_matrix(A, B):
    regsa = A.regions
    regsb = B.regions
    mat = np.zeros((len(regsa), len(regsb)))
    for x, y in it.product(range(mat.shape[0]), range(mat.shape[1])):
        mat[x, y] = cardinality_score(regsa[x], regsb[y])
    return mat


def establishment_matrix(A, B):
    mat = np.zeros((len(A), len(B)))

    coords = it.product(range(mat.shape[0]), range(mat.shape[1]))

    for i, coord in enumerate(coords):
        x, y = coord
        score_mat = score_matrix(A[x], B[y])
        mat[x, y] = np.max(score_mat)

        if not i % 200:
            print(f"{i} of {mat.size}...")

    return mat


def get_pointset(fname):
    ptset = []
    with open(fname) as f:
        for l in f:
            row = l.translate(str.maketrans('', '', '() '))
            row = row.split(',')
            ptset.append([
                float(Fraction(row[0])),
                float(row[2])
            ])
    return np.array(ptset)


def calculate_features(pat_list, ptset):
    feats = {}

    feats['num_patterns'] = len(pat_list)
    feats['avg_num_occurrences'] = np.mean([len(x.regions) for x in pat_list])
    feats['med_num_occurrences'] = np.median([len(x.regions) for x in pat_list])
    feats['max_cardinality'] = np.max([x.cardinality for x in pat_list])
    feats['mean_cardinality'] = np.mean([x.cardinality for x in pat_list])

    temp_dtype = {'names': ['f0', 'f1'], 'formats': [np.dtype('float64'), np.dtype('float64')]}
    all_regions = []
    for x in pat_list:
        all_regions += x.regions
    all_pts = np.concatenate(all_regions)

    overlap = np.intersect1d(all_pts.view(temp_dtype), ptset.view(temp_dtype))
    feats['coverage'] = len(overlap) / len(ptset)

    return feats

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    fnames = []
    for root, dirs, files in os.walk(r"./patterns_output"):
        for f in files:
            if f[-13:] == 'patterns.json':
                fnames.append(f[:f.index('_patterns')])

    all_feats = {}
    for fname in fnames:
        print(f'calculating features for {fname}...')
        pats = load_patterns(f'./patterns_output/{fname}_patterns.json')
        pts = get_pointset(f'./all_pointsets/{fname}_ptset.txt')

        all_feats[fname] = calculate_features(pats, pts)

    fkeys = list(all_feats[fnames[0]].keys())
    changes = {}
    for f in fnames:
        if 'omr' in f:
            f_prime = f.replace('omr', 'corrected')
            entry_name = f + '_to_corrected'
        elif 'corrected' in f:
            f_prime = f.replace('corrected', 'revised')
            entry_name = f + '_to_revised'
        elif 'revised' in f:
            f_prime = f.replace('corrected', 'aligned')
            entry_name = f + '_to_aligned'
        else:
            continue

        if f_prime not in fnames:
            changes[entry_name] = None
            continue

        c = {}
        for k in fkeys:
            orig_val = all_feats[f][k]
            ch_val = all_feats[f_prime][k]
            c[k] = ch_val / orig_val
        changes[entry_name] = c

    with open('./patcompare_results.csv', 'w', newline='') as csvfile:
        wr = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(['filename', 'stage'] + fkeys)
        for f in fnames:
            stage = f.split('_')[-1]
            wr.writerow([f, stage] + [all_feats[f][k] for k in fkeys])

    violin = {k: [[],[],[]] for k in fkeys}

    with open('./patcompare_changes.csv', 'w', newline='') as csvfile:
        wr = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(['filename', 'stage'] + fkeys)
        for f in changes.keys():
            stage = '_'.join(f.split('_')[-3:])

            if 'omr' in stage:
                v_ind = 0
            elif 'corrected' in stage:
                v_ind = 1
            else:
                v_ind = 2

            if not changes[f]:
                arr = [-1 for k in fkeys]
            else:
                arr = [changes[f][k] for k in fkeys]
                for k in fkeys:
                    violin[k][v_ind].append(changes[f][k])

            wr.writerow([f, stage] + arr)

    for k in fkeys:
        plt.clf()
            # Create a figure instance
        ax = plt.subplot(111)
        plt.violinplot(violin[k])
        ax.set_ylabel('Amount of change (multiplier)')
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(['OMR to Corrected', 'Corrected to Revised', 'Revised to Aligned'])
        plt.title(f'Change in {k}')
        plt.savefig(f'pat_changes_{k}.png')
