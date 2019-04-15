#! /usr/bin/env python3

import hfst
from sys import stderr
from math import log

eps = hfst.EPSILON
pad = '"<P>"'
lbreak = '<LBREAK>'

esc_dict = {
		'"': '%"',
		eps: '0',
		pad: pad,
		lbreak: '"'+lbreak+'"',
		'\\': '"\\\\"',
		}


def esc(char):
	if char in esc_dict:
		return esc_dict[char]
	return '{'+char+'}'


def get_total_freqs(pairs):
	total_freqs = {s1:0 for s1, s2 in pairs}
	for s1, s2 in pairs:
		total_freqs[s1] += 1
	return total_freqs


def get_freqs(pairs):
	freqs = {pair: 0 for pair in pairs}
	for pair in pairs:
		freqs[pair] += 1
	return freqs


def get_weights(aligned, smoothing):
	weights = {}
	pair_list = [pair for pairs in aligned for pair in pairs]
	freqs = get_freqs(pair_list)
	total_freqs = get_total_freqs(pair_list)
	for pair, freq in freqs.items():
		s1, s2 = pair
		w = 1 - freq/total_freqs[s1]
		if w < 0.95 and freq >= smoothing and s1 != eps:
			pair = esc(s1), esc(s2)
			weight = round(w, 4)
			weights[pair] = weight
	return weights


def get_regex(plist, smoothing):
	weights = get_weights(plist, smoothing)
	regex = '[ '
	for pair, weight in weights.items():
		s1, s2 = pair
		regex += '%s:%s::%s | ' % (s1, s2, weight)
	regex += '?::1.00 | ?:?::1.00 | ?:0::1.00 | 0:?::1.00 | 0:0::0.00 ]*'
	return regex


def build_aligner(aligned, smoothing=1):
	regex = get_regex(aligned, smoothing)
	return hfst.regex(regex)
