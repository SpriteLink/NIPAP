
DOCS=INSTALL.rst config-cli.rst config-nipapd.rst config-www.rst install-debian.rst install-unix.rst

all:
	for DOC in $(DOCS); do \
		OUT=`echo $$DOC | sed -e 's/.rst$$/.html/'`; \
		rst2html $$DOC | sed -ne '/<body/,/<\/body>/p' | \
		sed -e 's/<body>/---\n---\n{% include header.html %}\n<section><div class="container">/' | \
		sed -e 's/<\/body>/\n<\/div><\/section>{% include footer.html %}/' | \
		sed -e 's/href="\([^"]\+\).rst"/href="\1.html"/g' > $$OUT; \
	done

clean:
	for DOC in $(DOCS); do \
		OUT=`echo $$DOC | sed -e 's/.rst$$/.html/'`; \
		rm $$OUT; \
	done
