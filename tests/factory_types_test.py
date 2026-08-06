import typing as t

from envier import DerivedVariable
from envier import En
from envier import EnvVariable


class Config(En):
    required = En.var(int, "required")
    required_short = En.v(str, "required_short")
    derived = En.d(str, lambda _: "derived")


if t.TYPE_CHECKING:
    required: int = Config().required
    required_short: str = Config().required_short

    variable_items: t.Iterator[t.Tuple[str, EnvVariable[t.Any]]]
    variable_items = Config.items()
    variable_items = Config.items(include_derived=False)
    variable_items = Config.items(False, False)

    all_items: t.Iterator[
        t.Tuple[str, t.Union[EnvVariable[t.Any], DerivedVariable[t.Any]]]
    ]
    include_derived: bool = True
    all_items = Config.items(include_derived=True)
    all_items = Config.items(include_derived=include_derived)
    all_items = Config.items(False, True)
    all_items = Config.items(False, include_derived)
