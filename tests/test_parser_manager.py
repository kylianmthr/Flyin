import pytest
from contextlib import nullcontext as does_not_raise

from parser import (
    ConnectionValidator,
    DroneCountValidator,
    HubParser,
    Parser,
    ParserManager,
    StartOrEndHubValidator,
)


@pytest.mark.parametrize(
    "line, expectation, expected_return",
    [
        (
            "nb_drones: 3",
            does_not_raise(),
            {"parsed_and_validated_data": DroneCountValidator, "parser": "drone_count"},
        ),
        (
            "start_hub: start 0 0 [color=green]",
            does_not_raise(),
            {
                "parsed_and_validated_data": StartOrEndHubValidator,
                "parser": "start_hub",
            },
        ),
        (
            "hub: junction 1 0 [color=yellow max_drones=2]",
            does_not_raise(),
            {
                "parsed_and_validated_data": HubParser,
                "parser": "hub",
            },
        ),
        (
            "end_hub: goal 3 0 [color=red max_drones=3]",
            does_not_raise(),
            {
                "parsed_and_validated_data": StartOrEndHubValidator,
                "parser": "end_hub",
            },
        ),
        (
            "connection: start-junction",
            does_not_raise(),
            {
                "parsed_and_validated_data": ConnectionValidator,
                "parser": "connection",
            },
        ),
    ],
)
def test_open_file(line: str, expectation, expected_return: dict) -> None:
    with expectation:
        parser = ParserManager()
        res = parser.process(line)
        assert res == expected_return
