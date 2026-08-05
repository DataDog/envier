from typing import Optional

from envier import DerivedVariable
from envier import En
from envier import EnvVariable


class CustomObject(object):
    pass


def derive_custom_object(_: En) -> CustomObject:
    return CustomObject()


class Config(En):
    foo = En.v(str, "foo", default="hello")

    def derive_co(self: "Config") -> CustomObject:
        return CustomObject()

    def derive_foo(self: "Config") -> str:
        return self.foo

    co = En.d(CustomObject, derive_co)
    derived_foo = En.d(str, derive_foo)
    ignored_argument = En.d(bool, lambda _: True)
    opt: EnvVariable[Optional[str]] = En.v(Optional[str], "opt", default=None)
    opt_co: EnvVariable[Optional[CustomObject]] = En.var(
        Optional[CustomObject], "opt2", default=None
    )

    class SubConfig(En):
        __item__ = "subconfig"

        foo = En.v(str, "foo", default="hello")
        co = En.d(CustomObject, derive_custom_object)
        opt: EnvVariable[Optional[str]] = En.v(Optional[str], "opt", default=None)
        opt_co: EnvVariable[Optional[CustomObject]] = En.var(
            Optional[CustomObject], "opt2", default=None
        )

    subconfig: SubConfig


config = Config()

# Class and spec access expose the declarations.
foo_var: EnvVariable[str] = Config.foo
foo_spec_var: EnvVariable[str] = config.spec.foo
opt_var: EnvVariable[Optional[str]] = Config.opt
co_var: DerivedVariable[CustomObject] = Config.co
derived_foo: str = config.derived_foo
ignored_argument: bool = config.ignored_argument

# OK
config.foo = "world"
config.co = CustomObject()
config.opt = "False"
config.opt = None
config.opt_co = config.co
config.opt_co = None

config.subconfig.foo = "world"
config.subconfig.co = CustomObject()
config.subconfig.opt = "False"
config.subconfig.opt = None
config.subconfig.opt_co = config.co
config.subconfig.opt_co = None

# NOK
config.foo = 42
config.co = "CustomObject()"
config.opt = False
config.opt_co = b"hello"

config.subconfig.foo = 42
config.subconfig.co = "CustomObject()"
config.subconfig.opt = False
config.subconfig.opt_co = b"hello"
