.PHONY: install dev test commit help

install:
	@uv tool install . --force

dev:
	@uv pip install -e ".[dev]"

test:
	@pytest --cov=bmh --cov-report=term-missing

help:
	@bmh --help

commit:
	@echo "--- Conventional Commit Wizard ---"
	@echo "Types: feat, fix, docs, style, refactor, perf, test, chore"
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
