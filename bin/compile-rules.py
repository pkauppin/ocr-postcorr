#! /usr/bin/env python3
#
# - Compile parallel replace rules into a FST
# - Rules have been formulated in a way that allows them
#   to be compiled separately and then composed.
#   This is less time-consuming than compiling a single
#   monolithic rule set.
# - HFST is required for compilation and composition.

import hfst
from sys import argv, stderr

eps = hfst.EPSILON
pad = '"<P>"'

esc_dict = {
	'"': '%"',
	eps: '"<E>"',
	pad: pad,
	'\\': '"\\\\"',
	}


# Escape special characters
def esc(chars):
	S = []
	for char in chars.split(' '):
		if char in esc_dict:
			S.append(esc_dict[char])
		else:
			S.append('{%s}' % char)
	return ' '.join(S)


# Retrieve set of known characters from set of features
def get_chars(feats_file):
	file = open(feats_file, 'r')
	feats = [eval(line.strip()) for line in file]
	file.close()
	chars = { esc(pad) }
	for sub, cL, cR in feats:
		char = esc(sub[0])
		chars = chars | {char}
	return chars


def expand(fst):
	regex = '"<S>" -> [ "<S>" "<E>" "<.>" "<E>" "<S>" ]'
	fst.compose(hfst.regex(regex))


def serial_compile(regexs):

	# Compile each rule individually
	queue = [ ]
	for regex in regexs:
		fst = hfst.regex(regex)
		n = fst.number_of_states()
		queue.append(fst)
		
	# Sort resulting FST by number of states
	queue.sort(key=lambda fst: fst.number_of_states())

	# Compose smallest two, move resulting FST to end of queue
	n = len(queue)
	for i in range(n-1):
		fst1, fst2 = queue[0:2]
		fst1.compose(fst2)
		queue = queue[2:]+[fst1]
		queue.sort(key=lambda fst: fst.number_of_states())
	
	return queue[0]


def string2string(fst, rlist):

	eregex = [regex for regex in rlist if regex.startswith('"<E>"')]
	nregex = [regex for regex in rlist if regex not in eregex]

	stderr.write('Composing...\n')
	if nregex:
		fst.compose(serial_compile(nregex))
	if eregex:
		expand(fst)
		fst.compose(serial_compile(eregex))


def separators(fst):
	regex = '0 -> "<S>"'
	fst.compose(hfst.regex(regex))


def double(fst, chars):
	regex = '0 -> "<D>" "<.>" || "<S>" _ [ ? - "<S>" ] ,, 0 -> [ "<D>" "<.>" ] || .#. _ '
	fst.compose(hfst.regex(regex))
	rlist = ['"<D>" "<.>" %s -> %s "<.>" %s' % (c, c, c) for c in chars]
	regex = ' ,, '.join(rlist)
	fst.compose(hfst.regex(regex))


def single(fst, chars):
	regex = '"<S>" ? -> 0' 
	fst.compose(hfst.regex(regex))


def delete_aux(fst):
	regex = '[ "<P>" | "<S>" | "<E>" | "<D>" | "<.>" ] -> 0'
	fst.compose(hfst.regex(regex))


def compile(filename, outfile, feats_file):

	stderr.write('Compiling into FST...\n')

	rlist = open(filename, 'r', encoding='utf8').read().rstrip(' ;').split(',,\n')

	chars = get_chars(feats_file)

	fst = hfst.regex('0 -> "<S>"')
	fst.compose(hfst.regex('0 -> "<P>" || .#. _ ,, 0 -> "<P>" || _ .#.'))
	double(fst, chars)
	string2string(fst, rlist)

	# Delete preceding input-level symbol
	single(fst, chars)
	# Delete auxiliary symbols
	delete_aux(fst)
	# Minimize and write into .hfst file
	fst.minimize()
        
	fst.convert(hfst.ImplementationType.HFST_OLW_TYPE)

	ostr = hfst.HfstOutputStream(filename=outfile, type=hfst.ImplementationType.HFST_OLW_TYPE)
	ostr.write(fst)
	ostr.flush()
	ostr.close()
	stderr.write('Done.\n')


if __name__ == "__main__":
	argv.append(argv[1].replace('_regex.txt', '.hfst'))
	compile(argv[1], argv[2], argv[3])
