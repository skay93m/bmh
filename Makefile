.PHONY: install test help

install:
	@./install.sh

help:
	@bin/bmh --help

test:
	@bash -n bin/bmh
	@bash -n lib/ui.sh
	@echo "All shell syntax checks passed."
