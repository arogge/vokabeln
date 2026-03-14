ALL_PDFS := $(patsubst %.txt,%.pdf,$(wildcard *.txt))

.PHONY: all

all: $(ALL_PDFS)

%.pdf: %.txt
	./cards.py $< $@ 
