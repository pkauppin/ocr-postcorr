

ERRMODEL=errmodel.default.hfst
ACCEPTOR=acceptor.default.hfst

tr ' ' '\n' |
hfst-ospell -m -S $ERRMODEL -l $ACCEPTOR 
