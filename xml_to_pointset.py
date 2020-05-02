from music21 import *
from fractions import Fraction
import os

xmls = []
for root, dirs, files in os.walk(r"D:\Documents\felix_quartets_got_annotated"):
    for f in files:
        if f[-8:] == 'musicxml':
            xmls.append(os.path.join(root, f))

def is_onset(note):
    return ((note.tie is None) or (note.tie.type == 'start'))

def morphetic_pitch(note):
    morph_dict = {
        'C': 0,
        'D': 1,
        'E': 2,
        'F': 3,
        'G': 4,
        'A': 5,
        'B': 6,
    }

    n = note.pitch.name[0:1]
    oct = note.pitch.octave
    return (7 * oct) + morph_dict[n]

for fpath in xmls:

    print(f'parsing {fpath}...')
    xml = converter.parse(fpath)
    points = []

    for i, p in enumerate(xml.parts):
        for n in p.flat.notesAndRests:
            if n.isRest:
                continue
            elif n.isChord:
                points += [[i, n.offset, x.pitch.midi, morphetic_pitch(x)] for x in n.notes if is_onset(x)]
            elif is_onset(n):
                points.append([i, n.offset, n.pitch.midi, morphetic_pitch(n)])

    for p in points:
        p[1] += p[0] * 10000
        if p[1] == int(p[1]):
            p[1] = int(p[1])
        else:
            p[1] = Fraction(p[1]).limit_denominator(10)

    fname = fpath.split('\\')[-1][:-9] + r"_ptset.txt"
    out_path = os.path.join("./all_pointsets/", fname)
    with open(out_path, "w") as f:
        for p in points:
            f.write(f"({str(p[1])}, {p[2]}, {p[3]})\n")
