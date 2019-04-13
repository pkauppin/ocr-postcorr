#! /usr/bin/env python3

# Rewrite features as weighted parallel replace rules
# Only features whose frequency equals or exceeds a certain threshold value (by default 1) are accepted

from math import log10
from sys import argv, stderr

eps = '@_EPSILON_SYMBOL_@'
pad = '"<P>"'
sep = ' "<S>" '
lbreak = '<LBREAK>'

esc_dict = {
	'"': '%"',
	eps: '"<E>"',
	pad: pad,
	lbreak: '"'+lbreak+'"',
	'\\': '"\\\\"',
	}


# Escape special characters
def esc(s):
	if s in esc_dict:
		return esc_dict[s]
	return '{'+s.replace(' ', '')+'}'


# Retrieve feature tuples from input file
def get_feats(filename):
	file = open(filename, 'r')
	feats = [ eval(line.strip()) for line in file ]
	file.close()
	return feats


# Calculate feature frequencies and weights
def get_weights(feats, t=1):
	
	freqs = {feat:0 for feat in feats}
	for feat in feats:
		freqs[feat] += 1

	freqs = {feat:freq for feat, freq in freqs.items() if freq >= t}
	freqs = {feat:freq for feat, freq in freqs.items() if not (feat[0][0] == eps and feat[1:] == ((), (),))}   

	sums = {(s1, cL, cR,):0 for ((s1, s2), cL, cR,) in freqs}
	for feat, freq in freqs.items():
		((s1, s2), cL, cR,) = feat
		sums[( s1, cL, cR,)] += freq

	weights = {(s1, cL, cR,):{} for (s1, cL, cR,) in sums}
	for feat, freq in freqs.items():
		((s1, s2), cL, cR,) = feat
		w = -log10(freq / sums[( s1, cL, cR,)])
		weights[( s1, cL, cR,)][s2] = abs(round(w, 3))

	return weights


def ctext(c):
	return ' '.join([ esc(s) for s in c ])


def ctext_comp(c, epsilon=False):
	if len(c) == 0:
		return []
	return [ ' '+esc(s)+' "<.>" [ ? -'+sep+']* '  for s in c ]


def excl_str(excl):
	if len(excl) == 0:
		return ' '
	return ' [ ? - [ ' + ' | '.join([esc(s) for s in excl]) + ' ]] '


def excl_comp(excl):
	if len(excl) == 0:
		return []
	return [ ' [ ? - [  ' + ' | '.join([esc(s) for s in excl]) + ' ]] "<.>" [ ? -'+sep+']* ' ]


# If contexts overlap, return non-overlapping part(s) of said contexts
# Overlap on each side can only be 1 symbol/input segment long
def excess(q1, q2):
	(s1, cl1, cr1) = q1
	(s2, cl2, cr2) = q2
	clen1 = len(cl1) + len(cr1)
	clen2 = len(cl2) + len(cr2)
	ft1 = ''.join(cl1 + ('|', s1, '|') + cr1)
	ft2 = ''.join(cl2 + ('|', s2, '|') + cr2)
	if ft1 in ft2 and clen2 - clen1 == 1:
		return ft2.split(ft1)
	return [ '', '' ]


# Formulate negative contexts, return dictionary
def exclusions(weights):
	exc_dict = {}	
	for q1 in weights:
		excl_L = []
		excl_R = []
		for q2 in weights:
			[ xL, xR ] = excess(q1, q2)
			excl_L.append(xL)
			excl_R.append(xR)
		# Uniq by converting into set and back into list
		excl_L = sorted([ s for s in {z for z in excl_L} if s != ''])
		excl_R = sorted([ s for s in {z for z in excl_R} if s != ''])
		exc_dict[q1] = (excl_L, excl_R)
	return exc_dict


# Eliminate rules like a -> a::0.0 || ... – these will no longer be needed once negative contexts have been formulated
def remove_retentions(weights):
	return {(s, cL, cR):dict for (s, cL, cR), dict in weights.items() if dict != {s: 0.0}}


# Eliminate rule if overlapping rule with smaller context yields identical result
# This is to be done before formulating negative contexts
def generalize(weights):
	weights2 = weights
	for (s1, cL1, cR1), dict1 in weights.items():
		ft1 = ''.join(cL1 + ('|', s1, '|') + cR1)
		for (s2, cL2, cR2), dict2 in weights.items():
			ft2 = ''.join(cL2 + ('|', s2, '|') + cR2)
			if ft1 in ft2 and dict1 == dict2 and ft2 != ft1:
				weights2[( s2, cL2, cR2)] = {}
	return {(s, cL, cR):dict for (s, cL, cR), dict in weights2.items() if dict != {}}


def convert2regex_compressed(weights, excl):

	rules = []

	for (s1, cL, cR,), dict in weights.items():

		excl_L, excl_R = excl[(s1, cL, cR,)]

		s2 = ' | '.join(['%s::%s' % (esc(s), w) for s, w in dict.items()])

		cxL = ' "<S>" '.join(['%s <.> [ ? - "<S>"]*' % (esc(s)) for s in cL]) + ' "<S>"'
		cxR = '<.> %s "<S>" ' % (esc(s1)) + ' "<S>" '.join(['%s <.> [ ? - "<S>"]*' % (esc(s)) for s in cR])

		rules.append('%s -> [ %s ] ||\t%s _ %s' % (s1, s2, cxL.strip(), cxR.strip()))

	rules.sort()
	regex = ' ,,\n'.join(rules)+';'
	print(regex)
	stderr.write('Total number of rules: %i\n' % len(rules))
	return regex

		
# Weight and prune features, rewrite as rules
def get_rules(features, threshold=1):
	stderr.write('Writing replace rules, threshold: %i...\n' % threshold)
	weights = get_weights(features, threshold)
	weights = generalize(generalize(weights))
	excl_dict = exclusions(weights)
	weights = remove_retentions(weights)
	reg_expr = convert2regex_compressed(weights, excl_dict)


if __name__ == "__main__":
	argv.append(1)
	features = get_feats(argv[1])
	get_rules(features, int(argv[2]))
