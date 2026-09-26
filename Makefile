run:
	@uv run python -m src
debug:
	@uv run python -m pdb -m src
install:
	@uv sync
lint:
	@flake8 src
	@mypy src
clean:
	@pyclean .
