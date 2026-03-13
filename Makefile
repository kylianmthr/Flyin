NAME=flyin.py
MAP=maps/easy/01_linear_path.txt

all: ${NAME}

install:
	uv sync

run: ${NAME}
	uv run python ${NAME} ${MAP}

debug:
	uv run python -m pdb ${NAME} ${MAP}

clean:
	find . -iname "__pycache__" -type d -exec rm -rf "{}" +
	find . -iname ".mypy_cache" -type d -exec rm -rf "{}" +

lint:
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy .

#TODO: A SUPPRIMER
test:
	uv run pytest -vv

.PHONY: install run debug clean lint lint-strict test
