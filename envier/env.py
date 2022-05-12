import os
from typing import Callable
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union
import warnings


class NoDefaultType(object):
    pass


NoDefault = NoDefaultType()
DeprecationInfo = Tuple[str, str, str]


T = TypeVar("T")


class EnvVariable(Generic[T]):
    def __init__(self, type, name, parser=None, default=NoDefault, deprecations=None):
        # type: (Type[T], str, Optional[Callable[[str], T]], Union[T, NoDefaultType], Optional[List[DeprecationInfo]]) -> None
        if default is not NoDefault and not isinstance(default, type):
            raise TypeError("default must be of type {}".format(type))
        self.type = type
        self.name = name
        self.parser = parser
        self.default = default
        self.deprecations = deprecations

    def __call__(self, source, prefix):
        # type: (Dict[str, str], str) -> T
        raw = source.get(prefix + self.name)
        if raw is None and self.deprecations:
            for name, deprecated_when, removed_when in self.deprecations:
                raw = source.get(prefix + name)
                if raw is not None:
                    deprecated_when_message = (
                        " in version %s" % deprecated_when
                        if deprecated_when is not None
                        else ""
                    )
                    removed_when_message = (
                        " and will be removed in version %s" % removed_when
                        if removed_when is not None
                        else ""
                    )
                    warnings.warn(
                        "%s has been deprecated%s%s. Use %s instead"
                        % (
                            name,
                            deprecated_when_message,
                            removed_when_message,
                            self.name,
                        ),
                        DeprecationWarning,
                    )
                    break

        if raw is None:
            if not isinstance(self.default, NoDefaultType):
                return self.default

            raise KeyError("{} is not set".format(self.name))

        if self.parser is not None:
            parsed = self.parser(raw)
            if type(parsed) is not self.type:
                raise TypeError(
                    "parser returned type {} instead of {}".format(
                        type(parsed), self.type
                    )
                )
            return parsed

        return self.type(raw)  # type: ignore[call-arg]


class DerivedVariable(Generic[T]):
    def __init__(self, type, derivation):
        # type: (Type[T], Callable[[Env], T]) -> None
        self.type = type
        self.derivation = derivation

    def __call__(self, env):
        # type: (Env) -> T
        value = self.derivation(env)
        if not isinstance(value, self.type):
            raise TypeError(
                "derivation returned type {} instead of {}".format(
                    type(value), self.type
                )
            )
        return value


class Env(object):

    __prefix__ = ""

    def __init__(self):
        self.spec = self.__class__
        derived = []
        prefix = (
            self.__prefix__.upper().replace(".", "_").rstrip("_") + "_"
            if self.__prefix__
            else ""
        )
        for name, e in self.__class__.__dict__.items():
            if isinstance(e, EnvVariable) or isinstance(e, type) and issubclass(e, Env):
                setattr(self, name, e(os.environ, prefix))
            elif isinstance(e, DerivedVariable):
                derived.append((name, e))

        for n, d in derived:
            setattr(self, n, d(self))

    @classmethod
    def var(cls, type, name, parser=None, default=NoDefault, deprecations=None):
        # type: (Type[T], str, Optional[Callable[[str], T]], Union[T, NoDefaultType], Optional[List[DeprecationInfo]]) -> EnvVariable[T]
        return EnvVariable(type, name, parser, default, deprecations)

    @classmethod
    def der(cls, type, derivation):
        # type: (Type[T], Callable[[Env], T]) -> DerivedVariable[T]
        return DerivedVariable(type, derivation)
