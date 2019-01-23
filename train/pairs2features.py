#! /usr/bin/env python3

# Extract features from aligned string pairs
# Features are tuples the form ((input_symbol, output_symbol), left_hand_context, right_hand_context,)

from sys import argv, stderr

eps = '@_EPSILON_SYMBOL_@'
pad = '"<P>"'
lbreak = '<LBREAK>'
eps_pair = (eps, eps,)
pad_pair = (pad, pad,)

# Feature specifications:
# Features are specified by tuples of the form ( n, cL, cR ) where
# * n  = length of substituted segment i.e. number of symbols substituted
# * cL = length of left-hand context i.e. number of characters left of the substitution considered
# * cR = length of right-hand context i.e. number of characters right of the substitution considered 

feat_specs = {
    (1, 0, 0), # _
    (1, 1, 0), # x _
    (1, 1, 1), # x _ y
    (1, 1, 2), # x _ y z
    #(1, 2, 1), # x y _ z
    #(1, 0, 1), # _ x
    }

# Output extracted features
def print_feats(feats):
    for feat in feats:
        print(feat)


# Collapse sequences of consecutive insertions into single multichar insertions
def collapse_insertions(pairs):
    pairs_new = []
    prev = ''
    for i in range(len(pairs)-1):
        p_in  = pairs[i][0]
        p_out = pairs[i][1]
        if p_in == eps and pairs[i+1][0] == eps:
            prev += p_out + ' '
        else:
            p_out = prev + p_out
            pair_new = (p_in, p_out,)
            pairs_new.append(pair_new)
            prev = ''
    pairs_new.append(pairs[-1])
    return pairs_new


# Add input/output-level epsilons wherever needed 
def add_epsilons(pairs):
    pairs_new =[]
    for i in range(len(pairs)-1):
        pairs_new.append(pairs[i])
        if pairs[i+1][0] != eps and pairs[i][0] != eps:
            pairs_new.append(eps_pair)
    pairs_new.append(pairs[-1])
    return pairs_new


# Get symbols pairs form input file
# Convert plaintext data directly back into Python data structures
def get_pairs(filename):
    file = open(filename, 'r')
    plist = [ eval(line.strip()) for line in file ]
    file.close()
    return plist


# Loop over symbol pairs and feature specifications
# Return list of features (tuples)
def get_feats(pairs):
    feats = []
    for i in range(1, len(pairs)-1):
        for (s, lenL, lenR) in feat_specs:
            sub = pairs[i]
            xL = [ pair for pair in pairs[:i] if pair[0] != eps ]
            xR = [ pair for pair in pairs[i+1:] if pair[0] != eps ]
            if len(xL) >= lenL and len(xR) >= lenR:
                cxL = tuple( pair[0] for pair in xL[-lenL:] )
                cxR = tuple( pair[0] for pair in xR[:lenR] )
                if lenL == 0:
                    cxL = tuple()
                if lenR == 0:
                    cxR = tuple()
                feat = (sub, cxL, cxR,)
                feats.append(feat)
    return feats


def get_features(plist, print_out=False):
    stderr.write('Extracting features...\n')
    feats = []
    for pairs in plist:
        pairs = collapse_insertions(pairs)
        pairs = add_epsilons(pairs)
        feats += get_feats(pairs)
    feats.sort()
    stderr.write('%i features extracted in total.\n' % len(feats))
    if print_out:
        print_feats(feats)
    return feats


if __name__ == "__main__":
    plist = get_pairs(argv[1])
    get_features(plist, print_out=True)
