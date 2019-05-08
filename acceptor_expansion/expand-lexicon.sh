#!/bin/bash

LEXICON=$1

hfst-regexp2fst -S -i expand.regex > expand.hfst

hfst-project -i $LEXICON --project=UP |
hfst-compose expand.hfst |
hfst-minimize -E |
hfst-fst2fst -w
