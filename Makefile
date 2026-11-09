install:
	@uv sync
run:
	@uv run python -m src
debug:
	@uv run python -m pdb -m src
lint:
	@uv run flake8 src
	@uv run mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
clean:
	@pyclean .
	@rm -rf .mypy_cache
