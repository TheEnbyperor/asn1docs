import typing
import pyparsing
import dataclasses
from . import value, type, module

def assert_never(arg: typing.Any) -> typing.Never:
    raise AssertionError("Expected code to be unreachable")


@dataclasses.dataclass
class ReferenceParameter:
    is_value: bool
    value: typing.Union["type.Type", "value.Value"]

    @classmethod
    def build(
            cls, param: pyparsing.ParseResults, m: module.Module,
            parameters: typing.Optional[typing.Dict[str, "module.AssignmentParameter"]] = None
    ) -> "ReferenceParameter":
        if param.type:
            return cls(
                is_value=False,
                value=type.build_type(param.type[0], m, parameters)
            )
        elif param.value:
            return cls(
                is_value=True,
                value=value.build_value(param.value[0], m, parameters)
            )
        else:
            raise NotImplementedError(f"Unhandled parameter: {param}")