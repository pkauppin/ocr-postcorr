#! /usr/bin/env python3 

# Align pairs if strings on character/symbol level
# Return list of tuples of pairs of the form (input_level_symbol, ouput_level_symbol) 

import hfst
from sys import argv, stderr
from aligner import build_aligner

eps  = '@_EPSILON_SYMBOL_@'
pad  = '"<P>"'
lbreak   = '"<LBREAK>"'
eps_pair = (eps, eps,)
pad_pair = (pad, pad,)

tok = hfst.HfstTokenizer() # Default tokenizer
levenshtein = hfst.regex('[ ?::0 | ?:?::1 | 0:?::1 | ?:0::1 | 0:0::0 ]*')

cldict = {
    '\\':'\\\\',
    '\x84':'',
    }


#Remove and escape certain characters
def clean(str):
    for a, b in cldict.items():
        str = str.replace(a, b)
    return str


# Print aligned data
def print_pairs(plist):
    for pairs in plist:
        print(pairs)


#Extract pair tuples from FST
def get_pairs(fst):
    fst.n_best(1)
    p = fst.extract_paths(output='raw')[0][1]
    return ( pad_pair, ) + p + ( pad_pair, )


#Compile string to FST
def str2fst(str):
    tokenized = tok.tokenize(str)
    fst = hfst.tokenized_fst(tokenized)
    return fst


#Align string pair by FST composition
def align_strs(str1, str2, fst):
    tr1 = str2fst(str1)
    tr2 = str2fst(str2)
    tr1.compose(fst)
    tr1.compose(tr2)
    return get_pairs(tr1)


#Read data file and submit each string pair to alignment
def align_file(filename, fst):
    plist = []
    file = open(filename, 'r')
    for i, line in enumerate(file):
        line = line.strip('\n')
        try:
            str1, str2 = line.split('\t')[-2:]
            pairs = align_strs(clean(str1), clean(str2), fst)
            plist.append(pairs)
        except:
            if line != '':
                stderr.write('WARNING: Line %i has too few fields, skipping...\n' % (i+1))
    file.close()
    return plist


#...
def iterate(filename, iterations):
    fst = levenshtein
    for i in range(iterations):
        stderr.write('Aligning strings, iteration %i...\n' % (i+1))
        plist = align_file(filename, fst)
        fst = build_aligner(plist)
    return plist


#Main
def get_aligned(filename, iterations, print_out=False):
    plist = iterate(filename, iterations) 
    if print_out:
        print_pairs(plist)
    return plist


if __name__ == "__main__":
    get_aligned(argv[1], iterations=6, print_out=True)
