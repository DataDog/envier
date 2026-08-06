from typing import Optional

from envier import DerivedVariable
from envier import En
from envier import EnvVariable


class CustomObject(object):
    pass


class Config(En):
    foo = En.v(str, "foo", default="hello")

    def derive_co(self: "Config") -> CustomObject:
        return CustomObject()

    def derive_foo(self: "Config") -> str:
        return self.foo

    co = En.der(CustomObject, derive_co)
    derived_foo = En.d(str, derive_foo)
    opt: EnvVariable[Optional[str]] = En.v(Optional[str], "opt", default=None)
    opt_co: EnvVariable[Optional[CustomObject]] = En.var(
        Optional[CustomObject], "opt2", default=None
    )

    class SubConfig(En):
        __item__ = "subconfig"

        foo = En.v(str, "foo", default="hello")

    subconfig: SubConfig


config = Config()

# Class and spec access expose the declarations.
foo_var: EnvVariable[str] = Config.foo
foo_spec_var: EnvVariable[str] = config.spec.foo
co_var: DerivedVariable[CustomObject] = Config.co
derived_foo: str = config.derived_foo

# Instance access exposes values: these assignments must type-check.
config.foo = "world"
config.co = CustomObject()
config.opt = "False"
config.opt = None
config.opt_co = config.co
config.opt_co = None

config.subconfig.foo = "world"

# Each checker must reject all five invalid assignments below.
config.foo = 42
config.co = "CustomObject()"
config.opt = False
config.opt_co = b"hello"

config.subconfig.foo = 42
