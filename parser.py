from abc import ABC, abstractmethod
from typing import Optional, TypedDict
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    model_validator,
)
import re


class Parser:
    def __init__(self) -> None:
        self.content = ""

    def open(self, filename: str) -> None:
        """Open the map file that will be parsed

        Args:
            filename (str): The path to the map file
        Returns:
            str: The file content
        Raises:
            FileNotFound: The path to the file is incorrect
            PermissionError: The program can't access to the file
        """
        print(filename)
        with open(filename, "r") as f:
            self.content = f.read()

    def process(self) -> list[BaseModel]:
        res = []
        parser = ParserManager()
        blocks = self.content.split("\n\n")
        i = 0
        for block in blocks:
            block_content = []
            lines = block.split("\n")
            for line in lines:
                if not line.startswith("#") and len(line):
                    block_content.append(parser.process(line))
            i += 1
            res += block_content
            if i == 1:
                if block_content[0]["parser"] != "drone_count":
                    raise ValueError(
                        "Number of drone must be at the first line of the file"
                    )
        if i != 3:
            raise ValueError("Unexpected number of block")
        return res


class SpecificParser(ABC):
    @abstractmethod
    def process(self, line: str) -> dict:
        pass


class DroneCountParser(SpecificParser):
    def __init__(self) -> None:
        self._regex = re.compile(r"^nb_drones:\s+(?P<nbr>\d+)", re.M)

    def process(self, line: str) -> dict:
        match = self._regex.match(line)
        if not match:
            raise ValueError("Error: Line malformed.")
        obj = match.groupdict()
        obj["nbr"] = int(obj["nbr"])
        return obj


class StartHubParser(SpecificParser):
    def __init__(self) -> None:
        self._regex = re.compile(
            r"^start_hub:\s+(?P<id>\w+)\s+(?P<x>\d+)\s+(?P<y>\d+)(?P<extra>.*)$",
            re.M,
        )
        self._extra_regex = re.compile(
            r"^start_hub:\s+(?P<id>\w+)\s+(?P<x>\d+)\s+(?P<y>\d+)(?P<extra>.*)$",
            re.M,
        )

    def process(self, line: str) -> dict:
        match = self._regex.match(line)
        if not match:
            raise ValueError("Error: Line malformed.")
        obj = match.groupdict()
        obj.update({"color": None, "max_drones": -1})
        obj["x"] = int(obj["x"])
        obj["y"] = int(obj["y"])
        if not len(obj["extra"]):
            del obj["extra"]
            return obj
        extra = re.finditer(r"(?P<key>\w+)=(?P<value>\w+)", obj["extra"])
        for m in extra:
            if m.group("key") != "max_drones":
                obj[m.group("key")] = m.group("value")
        del obj["extra"]
        return obj


class HubParser(SpecificParser):
    def __init__(self) -> None:
        self._regex = re.compile(
            r"^hub:\s+(?P<id>\w+)\s+(?P<x>\d+)\s+(?P<y>\d+)(?P<extra>.*)$",
            re.M,
        )
        self._extra_regex = re.compile(
            r"^hub:\s+(?P<id>\w+)\s+(?P<x>\d+)\s+(?P<y>\d+)(?P<extra>.*)$",
            re.M,
        )

    def process(self, line: str) -> dict:
        match = self._regex.match(line)
        if not match:
            raise ValueError("Error: Line malformed.")
        obj = match.groupdict()
        obj.update({"color": None, "max_drones": None})
        obj["x"] = int(obj["x"])
        obj["y"] = int(obj["y"])
        if not len(obj["extra"]):
            del obj["extra"]
            return obj
        extra = re.finditer(r"(?P<key>\w+)=(?P<value>\w+)", obj["extra"])
        for m in extra:
            obj[m.group("key")] = m.group("value")
            if m.group("key") == "max_drones":
                obj["max_drones"] = int(obj["max_drones"])
        del obj["extra"]
        return obj


class EndHubParser(SpecificParser):
    def __init__(self) -> None:
        self._regex = re.compile(
            r"^end_hub:\s+(?P<id>\w+)\s+(?P<x>\d+)\s+(?P<y>\d+)(?P<extra>.*)$",
            re.M,
        )
        self._extra_regex = re.compile(
            r"^end_hub:\s+(?P<id>\w+)\s+(?P<x>\d+)\s+(?P<y>\d+)(?P<extra>.*)$",
            re.M,
        )

    def process(self, line: str) -> dict:
        match = self._regex.match(line)
        if not match:
            raise ValueError("Error: Line malformed.")
        obj = match.groupdict()
        obj.update({"color": None, "max_drones": -1})
        obj["x"] = int(obj["x"])
        obj["y"] = int(obj["y"])
        if not len(obj["extra"]):
            del obj["extra"]
            return obj
        extra = re.finditer(r"(?P<key>\w+)=(?P<value>\w+)", obj["extra"])
        for m in extra:
            if m.group("key") != "max_drones":
                obj[m.group("key")] = m.group("value")
        del obj["extra"]
        return obj


class ConnectionParser(SpecificParser):
    def __init__(self) -> None:
        self._regex = re.compile(
            r"^connection:\s+(?P<connection>\b\w+-\b\w+)", re.M
        )

    def process(self, line: str) -> dict:
        match = self._regex.match(line)
        if not match:
            raise ValueError("Error: Line malformed.")
        obj = match.groupdict()
        return obj


class DroneCountValidator(BaseModel):
    nbr: int = Field(ge=0)


class StartOrEndHubValidator(BaseModel):
    id: str = Field(min_length=1)
    x: int = Field(ge=0, le=40)
    y: int = Field(ge=0, le=40)
    color: Optional[str] = Field(default=None)
    max_drones: int = Field(ge=-1, le=-1)

    @model_validator(mode="after")
    def id_check(self: "StartOrEndHubValidator") -> "StartOrEndHubValidator":
        if "-" in self.id:
            raise ValueError("Error: id can't contain separator")
        return self


class HubValidator(BaseModel):
    id: str = Field(min_length=1)
    x: int = Field(ge=0, le=40)
    y: int = Field(ge=0, le=40)
    color: Optional[str] = Field(default=None)
    max_drones: Optional[int] = Field(default=None)

    @model_validator(mode="after")
    def id_check(self: "HubValidator") -> "HubValidator":
        if "-" in self.id:
            raise ValueError("Error: id can't contain separator")
        return self

    @model_validator(mode="after")
    def drones_check(self: "HubValidator") -> "HubValidator":
        if self.max_drones:
            if self.max_drones < 0:
                raise ValueError("Error: max_drones must be a positive number")
        return self

    @model_validator(mode="after")
    def already_exist(
        self: "HubValidator", info: ValidationInfo
    ) -> "HubValidator":
        if info.context:
            if self.id not in info.context["hubs"]:
                return self
            raise ValueError(f"Error: {self.id} hub already exist.")
        raise ValueError("Error: You must include context")


class ConnectionValidator(BaseModel):
    connection: str = Field(min_length=3)

    @model_validator(mode="after")
    def connection_check(
        self: "ConnectionValidator", info: ValidationInfo
    ) -> "ConnectionValidator":
        if "-" not in self.connection:
            raise ValueError("Error: Connections must include separator")
        if info.context:
            if self.connection not in info.context["connections"]:
                inverted_connection = "-".join(
                    self.connection.split("-")[::-1]
                )
                if inverted_connection not in info.context["connections"]:
                    if self.connection.split("-")[0] in info.context["hubs"]:
                        if (
                            self.connection.split("-")[1]
                            in info.context["hubs"]
                        ):
                            return self
                        raise ValueError(
                            f"Error: Trying to connect undeclared hub ({self.connection.split('-')[1]})"
                        )
                    raise ValueError(
                        f"Error: Trying to connect undeclared hub ({self.connection.split('-')[0]})"
                    )
                raise ValueError("Error: Duplicated connection")
            raise ValueError("Error: Duplicated connection")
        raise ValueError("Error: You must include context")


class ParsersDict(TypedDict):
    parser: SpecificParser
    validator: type[BaseModel]


class ParserManager:
    def __init__(self) -> None:
        self._parsers: dict[str, ParsersDict] = {
            "drone_count": {
                "parser": DroneCountParser(),
                "validator": DroneCountValidator,
            },
            "start_hub": {
                "parser": StartHubParser(),
                "validator": StartOrEndHubValidator,
            },
            "hub": {"parser": HubParser(), "validator": HubValidator},
            "end_hub": {
                "parser": EndHubParser(),
                "validator": StartOrEndHubValidator,
            },
            "connection": {
                "parser": ConnectionParser(),
                "validator": ConnectionValidator,
            },
        }
        self.hubs = []
        self.connections = []

    class ProcessedDict(TypedDict):
        parsed_and_validated_data: BaseModel
        parser: str

    def process(
        self,
        data: str,
    ) -> ProcessedDict | dict[str, Exception]:
        for parser in self._parsers:
            try:
                res = self._parsers[parser]["parser"].process(data)
                if parser == "connection":
                    validate_res = self._parsers[parser][
                        "validator"
                    ].model_validate(
                        res,
                        context={
                            "connections": self.connections,
                            "hubs": self.hubs,
                        },
                    )
                    self.connections.append(res["connection"])
                elif parser == "hub":
                    validate_res = self._parsers[parser][
                        "validator"
                    ].model_validate(res, context={"hubs": self.hubs})
                    self.hubs.append(res["id"])
                else:
                    if parser == "start_hub" or parser == "end_hub":
                        self.hubs.append(res["id"])
                    validate_res = self._parsers[parser]["validator"](**res)
                return {
                    "parsed_and_validated_data": validate_res,
                    "parser": parser,
                }
            except ValidationError as e:
                raise ValueError(e)
            except ValueError:
                pass
        raise ValueError(f"Unknown data: {data}")
