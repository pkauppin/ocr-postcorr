#! /usr/bin/env python3

import hfst, sys
from math import log

eps = '@_EPSILON_SYMBOL_@'
pad = '"<P>"'
lbreak = '<LBREAK>'

esc_dict = {
        '"'    : '%"',
        eps    : '0',
        pad    : pad,
        lbreak : '"'+lbreak+'"',
        '\\'   : '"\\\\"',
        }

# Escape special characters.
def esc(char):
    if char in esc_dict:
        return esc_dict[char]
    return '{'+char+'}'

def get_total_freqs(px):
    total_freqs = { p[0]:0 for p in px }
    for p in px:
        total_freqs[p[0]] += 1
    return total_freqs

def get_freqs(px):
    freqs = { p:0 for p in px }
    for p in px:
        freqs[p] += 1
    return freqs

def get_weights(plist, smoothing):
    weights = {}
    px = [ p for pairs in plist for p in pairs]
    freqs = get_freqs(px)
    total_freqs = get_total_freqs(px)
    for pair, freq in freqs.items():
        w = 1 - freq/total_freqs[pair[0]]
        if w < 0.95 and freq >= smoothing and pair[0] != eps:
            s1 = esc(pair[0])
            s2 = esc(pair[1])
            pair = (s1, s2,)
            weight = str(w+0.005)[:4]
            weights[pair] = weight
    return weights

def get_regex(plist, smoothing):
    weights = get_weights(plist, smoothing)
    regex = '[ '
    for pair, weight in weights.items():
        regex += pair[0]+':'+pair[1]+'::'+weight+' | '
    regex += '?::1.00 | ?:?::1.00 | ?:0::1.00 | 0:?::1.00 | 0:0::0.00 ]*'
    return regex

def build_aligner(plist, smoothing=3):
    regex = get_regex(plist, smoothing)
    fst = hfst.regex(regex)
    return fst
