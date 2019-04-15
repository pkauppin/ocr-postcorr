#!/usr/bin/env python3
# Align pairs of strings on character/symbol level.
# Return list of tuples of the form (input_level_symbol, ouput_level_symbol.
# String alignment is done iteratively:
# 1) Levenshtein distance is used for the initial alignment.
# 2) General edit distances are used for subsequent iterations.
# Distances/weights are (re)calculated from the aligned sting pairs after each iteration.
# This step is repeated until desired number of iterations has been reached.
#
# HFST is required for alignment.

import hfst
from sys import argv, stderr
from aligner import build_aligner
import argparse

eps = hfst.EPSILON
pad = '"<P>"'

eps_pair = (eps, eps,)
pad_pair = (pad, pad,)

tok = hfst.HfstTokenizer()
levenshtein = hfst.regex('[ ?::0 | ?:?::1 | 0:?::1 | ?:0::1 | 0:0::0 ]*')

cldict = {
	'\\': '\\\\',
	'\x84': '',
	}


def clean(s):

	"""
	Remove and escape certain characters
	"""

	for a, b in cldict.items():
		s = s.replace(a, b)
	return s


def print_pairs(plist):

	"""
	Print aligned data
	"""

	for pairs in plist:
		print(pairs)


def get_pairs(fst):

	"""
	Extract pair tuples from FST
	"""

	fst.n_best(1)
	p = list(fst.extract_paths(output='raw')[0][1])
	return [pad_pair] + p + [pad_pair]


def str2fst(str):

	"""
	Compile string to FST
	"""

	tokenized = tok.tokenize(str)
	fst = hfst.tokenized_fst(tokenized)
	return fst


def align_strs(str1, str2, aligner):

	"""
	Align string pair by FST composition
	"""

	tr1 = str2fst(str1)
	tr2 = str2fst(str2)
	fst = hfst.compose([tr1, aligner, tr2])
	return get_pairs(fst)


def align_file(filename, aligner):

	"""
	Read data file and submit each string pair to alignment
	"""

	plist = []
	file = open(filename, 'r')
	for i, line in enumerate(file, 1):
		line = line.strip('\n')
		try:
			str1, str2 = line.split('\t')[-2:]
			pairs = align_strs(clean(str1), clean(str2), aligner)
			plist.append(pairs)
		except:
			if line != '':
				stderr.write('WARNING: Line %s is missing fields, skipping...\n' % i)
	file.close()
	return plist


def iterate(filename, iterations):

	"""
	Align string pairs iteratively
	"""

	aligner_fst = levenshtein
	for i in range(iterations):
		stderr.write('Aligning strings, iteration %s...\n' % (i+1))
		pairs_list = align_file(filename, aligner_fst)
		aligner_fst = build_aligner(pairs_list)
	return pairs_list


def get_aligned(filename, iterations=6, print_out=False):

	"""
	Align tab-separated plaintext file
	"""

	plist = iterate(filename, iterations)
	stderr.write('%i string pairs aligned in total.\n' % len(plist))
	if print_out:
		print_pairs(plist)
	return plist


def main():
	parser = argparse.ArgumentParser(description="Align pairs of strings on character/symbol level. Return list of tuples of the form (input_level_symbol, ouput_level_symbol.")
	parser.add_argument('datafile', help='input data filename')
	parser.add_argument('--smooth', type=int, default=3, help='number of alignment iterations')
	parser.add_argument('--iters', type=int, default=6, help='smoothing used when recalculating weights for substitutions')
	args = parser.parse_args()
	get_aligned(args.datafile, iterations=args.iters, print_out=True)


if __name__ == "__main__":
	main()
