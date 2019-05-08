Expand finite-state lexicon or morphological analyzer into an FST that accept word forms with
- optional capitalization
- _w_ instead of _v_
- leading and trailing puncutuation

The resulting acceptor is the the HFST optimized lookup format.

Usage:

	./expand-lexicon.sh lexicon.hfst > lexicon-expanded.hfst