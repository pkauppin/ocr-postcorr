#! /usr/bin/env python3

# Rewrite features as weighted parallel replace rules
# Only features whose frequency equals or exceeds a certain threshold value (by default 1) are accepted

import hfst
from math import log10
from sys import argv, stderr
import argparse

eps = hfst.EPSILON
pad = '"<P>"'
sep = ' "<S>" '

esc_dict = {
	'"': '%"',
	eps: '"<E>"',
	pad: pad,
	'\\': '"\\\\"',
	}


def esc(s):

	"""
	Escape special characters
	"""

	if s in esc_dict:
		return esc_dict[s]
	return '{%s}' % s


def get_feats(filename):

	"""
	Retrieve feature tuples from input file
	"""

	file = open(filename, 'r')
	feats = [eval(line.strip()) for line in file]
	file.close()
	return feats


def get_weights(feats, t=1):

	"""
	Calculate feature frequencies and weights
	"""
	
	freqs = {feat: 0 for feat in feats}
	for feat in feats:
		freqs[feat] += 1

	freqs = {feat: freq for feat, freq in freqs.items() if freq >= t}

	# Disallow context-free insertions
	freqs = {feat: freq for feat, freq in freqs.items() if not (feat[0][0] == eps and feat[1:] == ((), (),))}

	sums = {(s1, cl, cr,): 0 for (s1, s2), cl, cr in freqs}
	for feat, freq in freqs.items():
		(s1, s2), cl, cr = feat
		sums[(s1, cl, cr,)] += freq

	weights = {(s1, cl, cr,): {} for (s1, cl, cr,) in sums}
	for feat, freq in freqs.items():
		(s1, s2), cl, cr = feat
		w = -log10(freq / sums[( s1, cl, cr,)])
		weights[(s1, cl, cr,)][s2] = abs(round(w, 3))

	return weights


def excl_regex(excl):
	if len(excl) == 0:
		return ''
	return '[? - [' + '|'.join([esc(s) for s in excl]) + ']]'


def excess(q1, q2):

	"""
	If contexts overlap, return non-overlapping part(s) of said contexts.
	Overlap on each side can only be 1 symbol/input segment long
	"""

	s1, cl1, cr1 = q1
	s2, cl2, cr2 = q2
	clen1 = len(cl1) + len(cr1)
	clen2 = len(cl2) + len(cr2)
	ft1 = ''.join(cl1 + ('|', s1, '|') + cr1)
	ft2 = ''.join(cl2 + ('|', s2, '|') + cr2)
	if ft1 in ft2 and clen2 - clen1 == 1:
		return ft2.split(ft1)
	return ['', '']


def exclusions(weights):

	"""
	Formulate negative contexts, return dictionary.
	"""

	exc_dict = {}	
	for q1 in weights:
		excl_l = []
		excl_r = []
		for q2 in weights:
			[ xl, xr ] = excess(q1, q2)
			excl_l.append(xl)
			excl_r.append(xr)
		# Uniq by converting into set and back into list
		excl_l = sorted([s for s in {z for z in excl_l} if s != ''])
		excl_r = sorted([s for s in {z for z in excl_r} if s != ''])
		exc_dict[q1] = (excl_l, excl_r)
	return exc_dict


def remove_retentions(weights):

	"""
	Eliminate rules like a -> a::0.0 || ...
	These will no longer be needed once the negative contexts have been formulated.
	"""

	return {(s, cl, cr):dict for (s, cl, cr), dict in weights.items() if dict != {s: 0.0}}


def generalize(weights):

	"""
	Eliminate a rule if an overlapping rule with a smaller context yields an identical result
	This should be done before formulating negative contexts.
	"""

	weights2 = weights
	for (s1, cl1, cr1), dict1 in weights.items():
		ft1 = ''.join(cl1 + ('|', s1, '|') + cr1)
		for (s2, cl2, cr2), dict2 in weights.items():
			ft2 = ''.join(cl2 + ('|', s2, '|') + cr2)
			if ft1 in ft2 and dict1 == dict2 and ft2 != ft1:
				weights2[( s2, cl2, cr2)] = {}
	return {(s, cl, cr):dict for (s, cl, cr), dict in weights2.items() if dict != {}}


def convert2regex_compressed(weights, excl):

	rules = []

	for (s1, cl, cr,), dict in weights.items():

		excl_l, excl_r = excl[(s1, cl, cr,)]

		cl = [esc(s) for s in cl]
		cr = [esc(s) for s in cr]
		if excl_l:
			cl = [excl_regex(excl_l)] + cl
		if excl_r:
			cr += [excl_regex(excl_r)]

		s1 = esc(s1)

		cxl = ' "<S>" '.join(['%s "<.>" [? - "<S>"]*' % s for s in cl]) + ' "<S>" %s "<.>" ' % s1
		cxr = ' "<S>" ' + ' "<S>" '.join(['%s "<.>" [? - "<S>"]*' % s for s in cr])

		if s1 == esc(eps):
			cxl = ' [ "<S>" "<E>" "<.>" "<E>" "<S>" ] '.join(['%s "<.>" [? - "<S>"]*' % s for s in cl]) + ' "<S>" %s "<.>" ' % s1
			cxr = ' "<S>" ' + ' [ "<S>" "<E>" "<.>" "<E>" "<S>" ] '.join(['%s "<.>" [? - "<S>"]*' % s for s in cr])

		s2 = ' | '.join(['%s::%s' % (esc(s), w) for s, w in dict.items()])

		rules.append('%s -> [ %s ] || %s _ %s' % (s1, s2, cxl.strip(), cxr.strip()))

	rules.sort()
	regex = ' ,,\n'.join(rules)+' ;'
	regex = regex.replace('"<.>" [? - "<S>"]* ,,', ',,')
	print(regex)
	stderr.write('Total number of rules: %i\n' % len(rules))
	return regex


def get_rules(features, threshold=1):

	"""
	1) Assign weights to features
	2) Discard redundant or anomalous features
	3) Rewrite as features as replace rules
	"""

	stderr.write('Writing replace rules, threshold: %i...\n' % threshold)
	weights = get_weights(features, threshold)
	weights = generalize(generalize(weights))
	excl_dict = exclusions(weights)
	weights = remove_retentions(weights)
	reg_expr = convert2regex_compressed(weights, excl_dict)
	return reg_expr

def main():
	argv.append(1)
	features = get_feats(argv[1])
	threshold = int(argv[2])
	get_rules(features, threshold)


if __name__ == "__main__":
	main()
