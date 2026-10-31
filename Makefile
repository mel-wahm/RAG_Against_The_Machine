install:
	@uv sync
run:
	@uv run python -m src
debug:
	@uv run python -m pdb -m src
lint:
	@flake8 src
	@mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
clean:
	@pyclean .
	@rm -rf .mypy_cache
