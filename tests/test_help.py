from envier import Env


class GlobalConfig(Env):
    __prefix__ = "myapp"

    debug_mode = Env.var(
        bool,
        "debug",
        default=False,
        help_type="Boolean",
        help="Whether to enable debug logging",
    )
    url = Env.var(
        str,
        "url",
        default="http://localhost:5000",
        help_type="String",
        help="The URL of the application.",
    )
    no_default = Env.var(
        str,
        "no_default",
        help_type="Boolean",
        help="A variable with no default value, which makes it mandatory",
    )

    class ServiceConfig(Env):
        __item__ = __prefix__ = "service"

        host = Env.var(
            str,
            "host",
            default="localhost",
            help="The host of the service.",
        )
        port = Env.var(
            int,
            "port",
            default=3000,
            help="The port of the service.",
        )


def test_help_info(monkeypatch):
    monkeypatch.setenv("MYAPP_NO_DEFAULT", "1")

    assert GlobalConfig.help_info() == [
        ("``MYAPP_DEBUG``", "Boolean", "False", "Whether to enable debug logging."),
        (
            "``MYAPP_NO_DEFAULT``",
            "Boolean",
            "",
            "A variable with no default value, which makes it mandatory.",
        ),
        (
            "``MYAPP_URL``",
            "String",
            "http://localhost:5000",
            "The URL of the application.",
        ),
    ]


def test_help_info_recursive(monkeypatch):
    monkeypatch.setenv("MYAPP_NO_DEFAULT", "1")

    assert GlobalConfig.help_info(recursive=True) == [
        ("``MYAPP_DEBUG``", "Boolean", "False", "Whether to enable debug logging."),
        (
            "``MYAPP_NO_DEFAULT``",
            "Boolean",
            "",
            "A variable with no default value, which makes it mandatory.",
        ),
        (
            "``MYAPP_URL``",
            "String",
            "http://localhost:5000",
            "The URL of the application.",
        ),
        ("``MYAPP_SERVICE_HOST``", "``str``", "localhost", "The host of the service."),
        ("``MYAPP_SERVICE_PORT``", "``int``", "3000", "The port of the service."),
    ]
