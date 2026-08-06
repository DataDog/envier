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
    items: t.Iterator[
        t.Tuple[str, t.Union[EnvVariable[t.Any], DerivedVariable[t.Any]]]
    ] = Config.items(include_derived=True)
