from typing import Any, ContextManager
from pydantic import ValidationError
import pytest
from contextlib import nullcontext as does_not_raise

from parser import (
    ConnectionValidator,
    DroneCountValidator,
    HubValidator,
    StartOrEndHubValidator,
)


@pytest.mark.parametrize(
    "parsed_dict, expectation, expected_validation",
    [
        ({"nbr": 2}, does_not_raise(), DroneCountValidator(nbr=2)),
        ({"nbr": "test"}, pytest.raises(ValidationError), None),
    ],
)
def test_validate_drone_count(
    parsed_dict: dict,
    expectation: ContextManager[Any],
    expected_validation: DroneCountValidator,
) -> None:
    with expectation:
        res = DroneCountValidator(**parsed_dict)
        assert expected_validation == res


@pytest.mark.parametrize(
    "parsed_dict, hubs_list, expectation",
    [
        (
            {
                "id": "start",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": -1,
            },
            [],
            does_not_raise(),
        ),
        (
            {
                "id": "start-hub",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": -1,
            },
            [],
            pytest.raises(ValidationError),
        ),
        (
            {"id": "start", "x": 0, "y": 0, "color": "green", "max_drones": 0},
            [],
            pytest.raises(ValidationError),
        ),
        (
            {
                "id": "start",
                "x": -1,
                "y": 0,
                "color": "green",
                "max_drones": -1,
            },
            [],
            pytest.raises(ValidationError),
        ),
        (
            {
                "id": "start",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": -1,
            },
            ["start"],
            pytest.raises(ValidationError),
        ),
    ],
)
def test_validate_start_hub(
    parsed_dict: dict, hubs_list: list[str], expectation: ContextManager[Any]
) -> None:
    with expectation:
        StartOrEndHubValidator.model_validate(
            parsed_dict, context={"hubs": hubs_list}
        )


@pytest.mark.parametrize(
    "parsed_dict, hubs_list, expectation",
    [
        (
            {"id": "test", "x": 0, "y": 0, "color": "green", "max_drones": -1},
            [],
            pytest.raises(ValidationError),
        ),
        (
            {
                "id": "start-hub",
                "x": 0,
                "y": 0,
                "color": "green",
                "max_drones": 2,
            },
            [],
            pytest.raises(ValidationError),
        ),
        (
            {"id": "start", "x": 0, "y": 0, "color": "green", "max_drones": 2},
            [],
            does_not_raise(),
        ),
        (
            {
                "id": "start",
                "x": -1,
                "y": 0,
                "color": "green",
                "max_drones": 2,
            },
            [],
            pytest.raises(ValidationError),
        ),
        (
            {"id": "start", "x": 0, "y": 0, "max_drones": 2},
            [],
            does_not_raise(),
        ),
        (
            {"id": "start", "x": 0, "y": 0},
            [],
            does_not_raise(),
        ),
        (
            {"id": "start", "x": 0, "y": 0, "color": "green", "max_drones": 2},
            ["start"],
            pytest.raises(ValidationError),
        ),
    ],
)
def test_validate_hub(
    parsed_dict: dict, hubs_list: list[str], expectation: ContextManager[Any]
) -> None:
    with expectation:
        HubValidator.model_validate(parsed_dict, context={"hubs": hubs_list})


@pytest.mark.parametrize(
    "parsed_dict, connections_list, hubs_list, expectation",
    [
        (
            {"connection": "test-test"},
            [],
            ["test", "test"],
            does_not_raise(),
        ),
        (
            {"connection": "test"},
            [],
            [],
            pytest.raises(ValidationError),
        ),
        (
            {"connection": "test1-test2"},
            ["test1-test2"],
            ["test1", "test2"],
            pytest.raises(ValidationError),
        ),
        (
            {"connection": "test1-test2"},
            ["test2-test1"],
            ["test1", "test2"],
            pytest.raises(ValidationError),
        ),
        (
            {"connection": "test2-test1"},
            ["test1-test2"],
            ["test1", "test2"],
            pytest.raises(ValidationError),
        ),
    ],
)
def test_validate_connection(
    parsed_dict: dict,
    connections_list: list,
    hubs_list: list[str],
    expectation: ContextManager[Any],
) -> None:
    with expectation:
        ConnectionValidator.model_validate(
            parsed_dict,
            context={"connections": connections_list, "hubs": hubs_list},
        )
