<h1 align="center">Envier</h1>
<h2 align="center">Python application configuration from the environment</h2>

## Synopsis

Envier is a Python library for extracting configuration from environment
variables in a declarative and (eventually) 12-factor-app-compliant way.


## Usage

The following example shows how to declare the configuration for an application
that uses the `MYAPP_DEBUG`, `MYAPP_SERVICE_HOST` and `MYAPP_SERVICE_PORT`
variables from the environment.

~~~ python
>>> from envier import Env
>>> 
>>> class GlobalConfig(Env):
>>>     __prefix__ = "myapp"
>>>     
>>>     debug_mode = Env.var(bool, "debug", default=False)
>>> 
>>>     service_host = Env.var(str, "service.host", default="localhost")
>>>     service_port = Env.var(int, "service.port", default=3000)
>>> 
>>>     def derive_is_default_port(config: "GlobalConfig") -> bool:
>>>         return config.service_port == config.spec.service_port.default
>>>
>>>     _is_default_port = Env.der(bool, derive_is_default_port)
>>> 
>>> config = GlobalConfig()
>>> config.service_port
3000
>>> config._is_default_port
True
~~~

Configurations can also be nested to create namespaces:

~~~ python
>>> from envier import Env
>>> 
>>> class ServiceConfig(Env):
>>>     __prefix__ = "service"
>>> 
>>>     host = Env.var(str, "host", default="localhost")
>>>     port = Env.var(int, "port", default=3000)
>>> 
>>> class GlobalConfig(Env):
>>>     __prefix__ = "myapp"
>>>     
>>>     debug_mode = Env.var(bool, "debug", default=False)
>>> 
>>>     service = ServiceConfig
>>> 
>>> config = GlobalConfig()
>>> config.service.port
3000
~~~

The same configuration can be obtained with implicit nesting by declaring the
`ServiceConfig` subclass inside `GlobalConfig`, and setting the class attribute
`__item__` to the name of the item the sub-configuration should be assigned to,
viz.

~~~ python
>>> from envier import Env
>>> 
>>> class GlobalConfig(Env):
>>>     __prefix__ = "myapp"
>>>     
>>>     debug_mode = Env.var(bool, "debug", default=False)
>>> 
>>>     class ServiceConfig(Env):
>>>         __item__ = __prefix__ = "service"
>>>         
>>>         host = Env.var(str, "host", default="localhost")
>>>         port = Env.var(int, "port", default=3000)
>>> 
>>> config = GlobalConfig()
>>> config.service.port
3000
~~~


## Type Checking

Variable and derived-value types are understood by both `mypy` and `pyright`.
Typing expressions such as `Optional[str]` should also have an explicit
attribute annotation so type checkers do not infer the type only from a
`None` default:

~~~python
from typing import Optional

from envier import Env
from envier import EnvVariable


class Config(Env):
    token: EnvVariable[Optional[str]] = Env.v(Optional[str], "token", default=None)
~~~

Derivation callbacks that access configuration fields should use a named
callback with an explicit parameter annotation, as in the synopsis above.
The enclosing class cannot be inferred from a lambda while its class body is
still being evaluated.

The library also ships with a `mypy` plugin for dynamically named nested
configurations. To use it, either install the library with the `mypy` extra or
ensure that `mypy` is installed, and then add `envier.mypy` to the list of extra
plugins in the `mypy` configuration. For portability to other type checkers,
nested configurations can instead be declared explicitly:

~~~python
class Config(Env):
    class Service(Env):
        __item__ = "service"

    service: Service
~~~


## Roadmap

- Add support for environment files.
- Rely on type hints as support for older versions of Python is dropped.
- Derivations might require an evaluation order.
