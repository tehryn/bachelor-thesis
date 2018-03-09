prezentace: xmatej52.pdf

xmatej52.pdf: xmatej52.tex
	pdflatex xmatej52.tex && pdflatex xmatej52.tex

.PHONY: clean zip prezentace
clean:
	rm -f xmatej52.pdf xmatej52.log xmatej52.aux xmatej52.toc xmatej52.out xmatej52.snm xmatej52.nav FIT-eps-converted-to.pdf
zip:
	zip xmatej52-fit.zip xmatej52.tex Makefile Debian.jpg mint.png ubuntu.png