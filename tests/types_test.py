from typing import Optional

from envier import En


class CustomObject(object):
    pass


class Config(En):
    foo = En.v(str, "foo", default="hello")
    co = En.d(CustomObject, lambda _: CustomObject())
    opt = En.v(Optional[str], "opt", default=None)
    opt_co = En.v(Optional[CustomObject], "opt2", default=None)

    class SubConfig(En):
        __item__ = "subconfig"

        foo = En.v(str, "foo", default="hello")
        co = En.d(CustomObject, lambda _: CustomObject())
        opt = En.v(Optional[str], "opt", default=None)
        opt_co = En.v(Optional[CustomObject], "opt2", default=None)


config = Config()

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
