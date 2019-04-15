#! /usr/bin/env python3

# Extract features from aligned string pairs
# Features are tuples the form ((input_symbol, output_symbol), left_hand_context, right_hand_context,)

import hfst
from sys import argv, stderr

eps = hfst.EPSILON
pad = '"<P>"'

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
	(1, 2, 1), # x y _ z
	(1, 0, 1), # _ x
	}


def print_feats(feats):

	"""
	Print extracted features to STDOUT
	"""

	for feat in feats:
		print(feat)


def collapse_insertions(pairs):

	"""
	Collapse sequences of consecutive insertions into single multi-char insertions
	"""

	pairs_new = []
	prev = ''
	for i in range(len(pairs)-1):
		p1_in, p1_out = pairs[i]
		p2_in, p2_out = pairs[i+1]
		if p1_in == eps and p2_in == eps:
			prev += p1_out
		else:
			p1_out = prev + p1_out
			pair_new = p1_in, p1_out,
			pairs_new.append(pair_new)
			prev = ''
	pairs_new.append(pairs[-1])
	return pairs_new


def add_epsilons(pairs):

	"""
	Add input/output-level epsilons wherever needed.
	"""

	pairs_new =[]
	for i in range(len(pairs)-1):
		pairs_new.append(pairs[i])
		if pairs[i+1][0] != eps and pairs[i][0] != eps:
			pairs_new.append(eps_pair)
	pairs_new.append(pairs[-1])
	return pairs_new


def get_pairs(filename):

	"""
	Get symbols pairs form input file.
	Convert plaintext data directly back into Python data structures.
	"""

	file = open(filename, 'r')
	pairs_list = [eval(line.strip()) for line in file]
	file.close()
	return pairs_list


def get_feats(pairs):

	"""
	Loop over symbol pairs and feature specifications.
	Return list of features (tuples).
	"""

	feats = []
	for i in range(1, len(pairs)-1):
		for (s, len_l, len_r) in feat_specs:
			sub = pairs[i]
			xl = [pair for pair in pairs[:i] if pair[0] != eps]
			xr = [pair for pair in pairs[i+1:] if pair[0] != eps]
			if len(xl) >= len_l and len(xr) >= len_r:
				cxl = tuple(pair[0] for pair in xl[-len_l:])
				cxr = tuple(pair[0] for pair in xr[:len_r])
				if len_l == 0:
					cxl = tuple()
				if len_r == 0:
					cxr = tuple()
				feat = sub, cxl, cxr
				feats.append(feat)
	return feats


def get_features(pairs_list, print_out=False):

	"""
	Extract desired features from the aligned data.
	The set of features that is extracted is determined by the feature specifications (feat_specs; see above)
	"""

	stderr.write('Extracting features...\n')
	feats = []
	for pairs in pairs_list:
		pairs = collapse_insertions(pairs)
		pairs = add_epsilons(pairs)
		feats += get_feats(pairs)
	feats.sort()
	stderr.write('%i tuples extracted in total.\n' % len(feats))
	if print_out:
		print_feats(feats)
	return feats


def main():
	pairs_list = get_pairs(argv[1])
	get_features(pairs_list, print_out=True)


if __name__ == "__main__":
	main()
