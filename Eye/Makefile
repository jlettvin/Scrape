DATETIME=`date +%Y%m%d%H%M%S`
MODULE=Eye
PDF=${MODULE}.pdf
OUT=${MODULE}.out
GIF=spine/spine.00.00.0100.gif
MAIN=${MODULE}.py

# Makefile
# __date__       = "20130101"
# __author__     = "jlettvin"
# __maintainer__ = "jlettvin"
# __email__      = "jlettvin@gmail.com"
# __copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
# __license__    = "Trade Secret"
# __status__     = "Production"
# __version__    = "0.0.1"

# Always make PDF last, since it terminates execution of make
all:	${GIF} ${OUT} ${PDF} Makefile

${OUT}:	${MAIN} Makefile
	@echo "\t${MAIN}"
	@- ./${MAIN}

${PDF}:	${MAIN} Makefile
	@echo "\t${PDF}"
	@- ./$< --pdf

${GIF}:	Spines.py Makefile
	@echo "\tSpines.py"
	@- ./$<

.PHONY: tgz
tgz:
	@echo ${DATETIME} incremental backup
	@tar cvzf tgz/${MODULE}.src.${DATETIME}.tgz . \
	  --exclude="*.tgz" \
	  --exclude="*.pyc" \
	  --exclude="tgz/*" \
	  --exclude="unsorted/*" \
	  --exclude="download/*" \
	  --exclude="tmp/*" \
	  --exclude="log/*" \
	  --exclude="img/*" \
	  --exclude="graph/*" \
	  --exclude="spine/*" \
	  --exclude="*.swp"

