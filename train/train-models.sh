#!/bin/bash
#
# This script trains a series of error models (unstructured classifiers)
# that can be used in simple string-to-string translation tasks.
# Intermediate files (string pairs, features, rule sets) are also created. 
#
# - Training data should be plaintext file of tab-separated pairs of strings
# - Feature extraction works as follows:
#     1) String pairs are aligned on character level.
#     2) Features (subsitutions + contexts) used by the unstructured classifier
#        are extracted. Feature specifications are hard-coded but can be modified.
# - Features whose frequency exceed $T are rewritten as weighted parallel-replace rules.
# - Replace rules are compiled into FSTs i.e. error models.
#
# Resulting error models can be used with e.g. hfst-ospell

BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

FNAME=$1

# Minimum and maximum thresholds
T_MIN=1
T_MAX=1

# Feature extraction
PFX=$( echo $FNAME | sed 's/\.[a-z][a-z][a-z]*$//g' )
PAIRS_FILE=$PFX\_pairs.txt
FEATS_FILE=$PFX\_feats.txt
$BASE/data2pairs.py $FNAME > $PAIRS_FILE
$BASE/pairs2features.py $PAIRS_FILE > $FEATS_FILE

# Rule formulation and compilation
for T in $( seq $T_MIN $T_MAX ) ; do
    REGEX_FILE=$PFX\_$T\_regex.txt
    OLFST_FILE=$PFX\_$T.hfst
    $BASE/features2rules.py $FEATS_FILE $T > $REGEX_FILE
    $BASE/compile-rules.py $REGEX_FILE $OLFST_FILE $FEATS_FILE
done
