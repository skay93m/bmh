.PHONY: install test commit help

install:
	@./install.sh

help:
	@bin/bmh --help

test:
	@bash -n bin/bmh
	@bash -n lib/ui.sh
	@echo "All shell syntax checks passed."

commit:
	@echo "--- Conventional Commit Wizard ---"
	@echo "Types: feat, fix, docs, style, refactor, perf, test, chore, bump"
	@read -p "Type: " type; \
	read -p "Scope (optional): " scope; \
	read -p "Short description: " desc; \
	if [ -n "$$scope" ]; then \
		msg="$$type($$scope): $$desc"; \
	else \
		msg="$$type: $$desc"; \
	fi; \
	echo "Committing: $$msg"; \
	git commit -m "$$msg"
