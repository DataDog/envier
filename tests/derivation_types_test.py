import typing as t

from envier import En


class OtherConfig(En):
    other = En.v(str, "other", default="other")


def derive_expected(config: "GoodConfig") -> str:
    return config.value


def derive_other(config: OtherConfig) -> str:
    return config.other


class GoodConfig(En):
    value = En.v(str, "value", default="value")
    derived = En.d(str, derive_expected)


class BadConfig(En):
    derived = En.d(str, derive_other)


if t.TYPE_CHECKING:
    good_value: str = GoodConfig().derived
    bad_value: str = BadConfig().derived
