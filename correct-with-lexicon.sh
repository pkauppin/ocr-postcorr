#!/bin/bash

ERRMODEL=$1
ACCEPTOR=$2

tr ' ' '\n' |
hfst-ospell -S -m $ERRMODEL -l $ACCEPTOR 
