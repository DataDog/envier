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
>>>     _is_default_port = Env.der(bool, lambda c: c.service_port == c.spec.service_port.default)
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


## Roadmap

- Add support for environment files.
- Rely on type hints as support for older versions of Python is dropped.
- Derivations might require an evaluation order.
