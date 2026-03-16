import pytest
from contextlib import nullcontext as does_not_raise

from parser import (
    ConnectionValidator,
    DroneCountValidator,
    HubParser,
    HubValidator,
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
            {
                "parsed_and_validated_data": DroneCountValidator,
                "parser": "drone_count",
            },
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
                "parsed_and_validated_data": HubValidator,
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
            "connection: truc-jsp",
            does_not_raise(),
            {
                "parsed_and_validated_data": ConnectionValidator,
                "parser": "connection",
            },
        ),
    ],
)
def test_choose_right_parser(
    line: str, expectation, expected_return: dict
) -> None:
    with expectation:
        parser = ParserManager()
        parser.hubs = ["truc", "jsp"]
        res = parser.process(line)
        assert res["parser"] == expected_return["parser"]
        assert isinstance(
            res["parsed_and_validated_data"],
            expected_return["parsed_and_validated_data"],
        )
