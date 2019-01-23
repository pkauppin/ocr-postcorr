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
    '"'    : '%"',
    eps    : '"<E>"',
    pad    : pad,
    lbreak : '"'+lbreak+'"'
    '\\'   : '"\\\\"',
    }


def esc(s):
    if s in esc_dict:
        return esc_dict[s]
    return '{'+s.replace(' ', '')+'}'


# Open list of simple rules.
def get_feats(filename):
    file = open(filename, 'r')
    feats = [ eval(line.strip()) for line in file ]
    file.close()
    return feats


def get_weights(feats, t=1):
    
    freqs = { feat:0 for feat in feats }
    for feat in feats:
        freqs[feat] += 1

    freqs = { feat:freq for feat, freq in freqs.items() if freq >= t }
    freqs = { feat:freq for feat, freq in freqs.items() if not ( feat[0][0] == eps and feat[1:] == ( (), (), ) ) }   

    sums = { ( s1, cL, cR, ):0 for ( (s1, s2), cL, cR, ) in freqs }
    for feat, freq in freqs.items():
        ( (s1, s2), cL, cR, ) = feat
        sums[( s1, cL, cR, )] += freq

    weights = { ( s1, cL, cR, ):{} for ( s1, cL, cR, ) in sums }
    for feat, freq in freqs.items():
        ( (s1, s2), cL, cR, ) = feat
        w = -log10(freq / sums[( s1, cL, cR, )])
        weights[( s1, cL, cR, )][s2] = round(w, 3)

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
    ( s1, cl1, cr1 ) = q1
    ( s2, cl2, cr2 ) = q2
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
        excl_L = sorted([ s for s in { z for z in excl_L } if s != ''])
        excl_R = sorted([ s for s in { z for z in excl_R } if s != ''])
        exc_dict[q1] = ( excl_L, excl_R )
    return exc_dict


# Eliminate rules like a -> a::0.0 || ... – these will no longer be needed once negative contexts have been formulated
def remove_retentions(weights):
    return { ( s, cL, cR ):dict for ( s, cL, cR ), dict in weights.items() if dict != { s : 0.0 } }


# Eliminate rule if overlapping rule with smaller context yields identical result
# This is to be done before formulating negative contexts
def generalize(weights):
    weights2 = weights
    for ( s1, cL1, cR1 ), dict1 in weights.items():
        ft1 = ''.join(cL1 + ('|', s1, '|') + cR1)
        for ( s2, cL2, cR2 ), dict2 in weights.items():
            ft2 = ''.join(cL2 + ('|', s2, '|') + cR2)
            if ft1 in ft2 and dict1 == dict2 and ft2 != ft1:
                weights2[( s2, cL2, cR2)] = {}
    return { ( s, cL, cR ):dict for ( s, cL, cR ), dict in weights2.items() if dict != {} }


def convert2regex(weights, excl):
    rules = []
    for ( s1, cL, cR, ), dict in weights.items():
        subst = esc(s1) + " -> [ " + " | ".join(sorted([ esc(s2)+"::"+str(w) for s2, w in dict.items() ])) + " ]\t"
        ( excl_L, excl_R ) = excl[(s1, cL, cR,)]
        context = excl_str(excl_L) + ctext(cL) + ' _ ' + ctext(cR) + excl_str(excl_R)
        rules.append([(s1, cL, cR), subst + '||' + context])
    rules.sort()
    rules = [ r[1] for r in rules ][::-1]
    regex = ',,\n'.join(rules)+';'
    regex = regex.replace('  ', ' ')
    regex = regex.replace('"<E>"', '0')
    regex = regex.replace('"<P>"', '.#.')
    print(regex)
    print('# Rules:',len(rules))
    return regex


def convert2regex_compressed(weights, excl):
    rules = []
    for ( s1, cL, cR, ), dict in weights.items():
        subst = esc(s1) + " -> [ " + " | ".join(sorted([ esc(s2)+"::"+str(w) for s2, w in dict.items() ])) + " ]\t"
        ( excl_L, excl_R ) = excl[(s1, cL, cR,)]
        if s1 == eps:
            ctextL = (sep+'"<E>" "<.>" [ ? -'+sep+']*'+sep).join(excl_comp(excl_L) + ctext_comp(cL))
            ctextR = (sep+'"<E>" "<.>" [ ? -'+sep+']*'+sep).join(ctext_comp(cR) + excl_comp(excl_R))
        else:
            ctextL = sep.join(excl_comp(excl_L) + ctext_comp(cL))
            ctextR = sep.join(ctext_comp(cR) + excl_comp(excl_R))
        context = ctextL + sep + esc(s1) + ' "<.>" _' + sep + ctextR
        rules.append([(s1, cL, cR), subst + '||' + context])
    rules.sort()
    rules = [ r[1] for r in rules ][::-1]
    regex = ',,\n'.join(rules)+';'
    #Cleanup:
    regex = regex.replace('  ', ' ')
    regex = regex.replace('"<.>" [ ? -'+sep+']*'+sep+',,', '"<.>" ,,')
    regex = regex.replace('"<.>" [ ? -'+sep+']*'+sep+';', '"<.>" ;')
    regex = regex.replace('"<.>" [ ? -'+sep+']* ,,', '"<.>" ,,')
    regex = regex.replace('"<.>" [ ? -'+sep+']* ;', '"<.>" ;')
    regex = regex.replace('|| ', '||'+sep)
    regex = regex.replace('"<S>" "<S>"', '"<S>"')
    #Optional (?):
    regex = regex.replace('"<.>" [ ? - "<S>" ]*', '[ ? ]') # <- !!!
    regex = regex.replace(' "<.>"', ' ')
    regex = regex.replace('[ ? - "<S>" ]*', '[ ? ]')
    regex = regex.replace('  ', ' ')
    print(regex)
    stderr.write('N° of rules: %i\n' % len(rules))
    return regex

        
# main
def get_rules(features, threshold):
    weights   = get_weights(features, threshold)
    weights   = generalize(generalize(weights))
    excl_dict = exclusions(weights)
    weights   = remove_retentions(weights)
    reg_expr  = convert2regex_compressed(weights, excl_dict)

argv.append(1)

if __name__ == "__main__":
    features  = get_feats(argv[1])
    get_rules(features, int(argv[2]))