#!/bin/bash
ERRMODEL=$1

tr ' ' '\n' |
hfst-lookup -n 1000 $ERRMODEL 
