from typing import Any, ContextManager
from parser import (
    Parser,
)
import pytest
from contextlib import nullcontext as does_not_raise


@pytest.mark.parametrize(
    "path, expectation",
    [
        (
            "maps/easy/01_linear_path.txt",
            does_not_raise(),
        ),
        (
            "maps/easy/02_simple_fork.txt",
            does_not_raise(),
        ),
        (
            "maps/easy/03_basic_capacity.txt",
            does_not_raise(),
        ),
        (
            "maps/medium/01_dead_end_trap.txt",
            does_not_raise(),
        ),
        (
            "maps/medium/02_circular_loop.txt",
            does_not_raise(),
        ),
        (
            "maps/medium/03_priority_puzzle.txt",
            does_not_raise(),
        ),
        (
            "maps/hard/01_maze_nightmare.txt",
            does_not_raise(),
        ),
        (
            "maps/hard/02_capacity_hell.txt",
            does_not_raise(),
        ),
        (
            "maps/hard/03_ultimate_challenge.txt",
            does_not_raise(),
        ),
    ],
)
def test_with_real_files(path: str, expectation: ContextManager[Any]) -> None:
    """Checks that parser can open each bundled map file.

    Args:
        path: Map path under test.
        expectation: Context manager defining expected outcome.
    """
    with expectation:
        parser = Parser()
        parser.open(path)
