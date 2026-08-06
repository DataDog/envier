import typing as t

from envier import DerivedVariable
from envier import En
from envier import EnvVariable


VariableItem = t.Tuple[str, EnvVariable[t.Any]]
DeclarationItem = t.Tuple[str, t.Union[EnvVariable[t.Any], DerivedVariable[t.Any]]]


class Config(En):
    required = En.var(int, "required")
    required_short = En.v(str, "required_short")
    derived = En.d(str, lambda _: "derived")


if t.TYPE_CHECKING:
    # A required variable infers its value type without a default or parser.
    required: int = Config().required
    required_short: str = Config().required_short
    derived: str = Config().derived

    # Omitting include_derived, or passing False, keeps the narrow item type.
    default_items: t.Iterator[VariableItem] = Config.items()
    keyword_variable_items: t.Iterator[VariableItem] = Config.items(
        include_derived=False
    )
    positional_variable_items: t.Iterator[VariableItem] = Config.items(False, False)

    # A runtime bool may include either kind of declaration.
    def check_runtime_bool(include_derived: bool) -> None:
        keyword_items: t.Iterator[DeclarationItem] = Config.items(
            include_derived=include_derived
        )
        positional_items: t.Iterator[DeclarationItem] = Config.items(
            False, include_derived
        )
