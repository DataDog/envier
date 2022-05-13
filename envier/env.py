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
from typing import cast
import warnings


class NoDefaultType(object):
    pass


NoDefault = NoDefaultType()
DeprecationInfo = Tuple[str, str, str]


T = TypeVar("T")


def _normalized(name):
    # type: (str) -> str
    return name.upper().replace(".", "_").rstrip("_")


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

    def __call__(self, env, prefix):
        # type: (Env, str) -> T
        source = env.source

        raw = source.get(prefix + _normalized(self.name))
        if raw is None and self.deprecations:
            for name, deprecated_when, removed_when in self.deprecations:
                raw = source.get(prefix + _normalized(name))
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

        if self.type is bool:
            return cast(T, raw.lower() in env.__truthy__)

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
    """Env base class.

    This class is meant to be subclassed. The configuration is declared by using
    the ``Env.var`` and ``Env.der`` class methods. The former declares a mapping
    between attributes of the instance of the subclass with the environment
    variables. The latter declares derived attributes that are computed using
    a given derivation function.

    If variables share a common prefix, this can be specified with the
    ``__prefix__`` class attribute. Any dots in the prefix or the variable names
    will be replaced with underscores. The variable names will be uppercased
    before being looked up in the environment.

    By default, boolean variables evaluate to true if their lower-case value is
    one of ``true``, ``yes``, ``on`` or ``1``. This can be overridden by either
    passing a custom parser to the variable declaration, or by overriding the
    ``__truthy__`` class attribute, which is a set of lower-case strings that
    are considered to be a representation of ``True``.
    """

    __truthy__ = frozenset({"1", "true", "yes", "on"})
    __prefix__ = ""

    def __init__(self, source=None, parent=None):
        # type: (Optional[Dict[str, str]], Optional[Env]) -> None
        self.source = source or os.environ
        self.parent = parent

        self._full_prefix = (
            parent._full_prefix if parent is not None else ""
        ) + _normalized(
            self.__prefix__
        )  # type: str
        if self._full_prefix:
            self._full_prefix += "_"

        self.spec = self.__class__
        derived = []
        for name, e in self.__class__.__dict__.items():
            if isinstance(e, EnvVariable):
                setattr(self, name, e(self, self._full_prefix))
            elif isinstance(e, type) and issubclass(e, Env):
                setattr(self, name, e(source, self))
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

    v = var
    d = der

    @classmethod
    def include(cls, env_spec, namespace=None, overwrite=False):
        # type: (Type[Env], Optional[str], bool) -> None
        """Include variables from another Env subclass.

        The new items can be merged at the top level, or parented to a
        namespace. By default, the method raises a ``ValueError`` if the
        operation would result in some variables being overwritten. This can
        be disabled by setting the ``overwrite`` argument to ``True``.
        """
        if namespace is not None:
            if not overwrite and hasattr(cls, namespace):
                raise ValueError("Namespace already in use: {}".format(namespace))

            setattr(cls, namespace, env_spec)

        # Pick only the attributes that define variables.
        to_include = {
            k: v
            for k, v in env_spec.__dict__.items()
            if isinstance(v, (EnvVariable, DerivedVariable))
            or isinstance(v, type)
            and issubclass(v, Env)
        }

        if not overwrite:
            overlap = set(cls.__dict__.keys()) & set(to_include.keys())
            if overlap:
                raise ValueError("Configuration clashes detected: {}".format(overlap))

        for k, v in to_include.items():
            setattr(cls, k, v)
