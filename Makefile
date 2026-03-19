NAME=flyin.py
#MAP=maps/easy/01_linear_path.txt
MAP=maps/challenger/01_the_impossible_dream.txt
#MAP=maps/easy/03_basic_capacity.txt
#MAP=maps/hard/02_capacity_hell.txt
#MAP=maps/challenger/01_the_impossible_dream.txt

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
	uv run flake8 . --exclude .venv
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude .venv

lint-strict:
	uv run flake8 . --exclude .venv
	uv run mypy . --exclude .venv

#TODO: A SUPPRIMER
test:
	uv run pytest -vv

.PHONY: install run debug clean lint lint-strict test
