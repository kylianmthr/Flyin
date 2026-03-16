from typing import Any, ContextManager
from parser import (
    ConnectionParser,
    DroneCountParser,
    EndHubParser,
    HubParser,
    Parser,
    StartHubParser,
)
import pytest
from contextlib import nullcontext as does_not_raise


@pytest.mark.parametrize(
    "path, expectation",
    [
        ("maps/easy/01_linear_path.txt", does_not_raise()),
        ("maps/easy/02_unknown_map.txt", pytest.raises(FileNotFoundError)),
    ],
)
def test_open_file(path: str, expectation: ContextManager[Any]) -> None:
    with expectation:
        Parser().open(path)


@pytest.mark.parametrize(
    "line, expectation, expected_output",
    [
        ("nb_drones: 3", does_not_raise(), {"nbr": 3}),
        ("test", pytest.raises(ValueError), None),
        ("test: r", pytest.raises(ValueError), None),
    ],
)
def test_parse_drone_number(
    line: str, expectation: ContextManager[Any], expected_output: dict | None
) -> None:
    with expectation:
        res = DroneCountParser().process(line)
        assert res == expected_output


@pytest.mark.parametrize(
    "line, expectation, expected_output",
    [
        (
            "start_hub: start 0 0 [color=green]",
            does_not_raise(),
            {
                "id": "start",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": -1,
            },
        ),
        (
            "start_hub: start 0 0",
            does_not_raise(),
            {"id": "start", "x": 0, "y": 0, "color": None, "max_drones": -1},
        ),
        (
            "start_hub: start 0 0 [max_drones=5]",
            does_not_raise(),
            {"id": "start", "x": 0, "y": 0, "color": None, "max_drones": -1},
        ),
        (
            "start_hub: start 0 0 [color=green max_drones=5]",
            does_not_raise(),
            {
                "id": "start",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": -1,
            },
        ),
        ("test", pytest.raises(ValueError), None),
        ("test: r", pytest.raises(ValueError), None),
    ],
)
def test_parse_start_hub(
    line: str, expectation: ContextManager[Any], expected_output: dict | None
) -> None:
    with expectation:
        res = StartHubParser().process(line)
        assert res == expected_output


@pytest.mark.parametrize(
    "line, expectation, expected_output",
    [
        (
            "hub: waypoint 0 0 [color=green]",
            does_not_raise(),
            {
                "id": "waypoint",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": None,
                "zone": "normal",
            },
        ),
        (
            "hub: waypoint 0 0",
            does_not_raise(),
            {
                "id": "waypoint",
                "x": 0,
                "y": 0,
                "color": None,
                "zone": "normal",
                "max_drones": None,
            },
        ),
        (
            "hub: waypoint 0 0 [max_drones=5]",
            does_not_raise(),
            {
                "id": "waypoint",
                "x": 0,
                "y": 0,
                "color": None,
                "max_drones": 5,
                "zone": "normal",
            },
        ),
        (
            "hub: waypoint 0 0 [color=green max_drones=5]",
            does_not_raise(),
            {
                "id": "waypoint",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": 5,
                "zone": "normal",
            },
        ),
        (
            "hub: waypoint 0 0 [color=green zone=restricted max_drones=5]",
            does_not_raise(),
            {
                "id": "waypoint",
                "x": 0,
                "y": 0,
                "color": "green",
                "zone": "restricted",
                "max_drones": 5,
            },
        ),
        ("test", pytest.raises(ValueError), None),
        ("test: r", pytest.raises(ValueError), None),
    ],
)
def test_parse_hub(
    line: str, expectation: ContextManager[Any], expected_output: dict | None
) -> None:
    with expectation:
        res = HubParser().process(line)
        assert res == expected_output


@pytest.mark.parametrize(
    "line, expectation, expected_output",
    [
        (
            "end_hub: goal 0 0 [color=green]",
            does_not_raise(),
            {"id": "goal", "x": 0, "y": 0, "color": "green", "max_drones": -1},
        ),
        (
            "end_hub: goal 0 0",
            does_not_raise(),
            {"id": "goal", "x": 0, "y": 0, "color": None, "max_drones": -1},
        ),
        (
            "end_hub: goal 0 0 [max_drones=5]",
            does_not_raise(),
            {"id": "goal", "x": 0, "y": 0, "color": None, "max_drones": -1},
        ),
        (
            "end_hub: goal 0 0 [color=green max_drones=5]",
            does_not_raise(),
            {"id": "goal", "x": 0, "y": 0, "color": "green", "max_drones": -1},
        ),
        ("test", pytest.raises(ValueError), None),
        ("test: r", pytest.raises(ValueError), None),
    ],
)
def test_parse_end_hub(
    line: str, expectation: ContextManager[Any], expected_output: dict | None
) -> None:
    with expectation:
        res = EndHubParser().process(line)
        assert res == expected_output


@pytest.mark.parametrize(
    "line, expectation, expected_output",
    [
        (
            "connection: test-test",
            does_not_raise(),
            {"connection": "test-test"},
        ),
        ("test", pytest.raises(ValueError), None),
        ("connection: test", pytest.raises(ValueError), None),
        ("test: r", pytest.raises(ValueError), None),
    ],
)
def test_parse_connection(
    line: str, expectation: ContextManager[Any], expected_output: dict | None
) -> None:
    with expectation:
        res = ConnectionParser().process(line)
        assert res == expected_output
