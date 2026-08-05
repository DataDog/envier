import typing as t

from mypy.nodes import AssignmentStmt
from mypy.nodes import ClassDef
from mypy.nodes import StrExpr
from mypy.plugin import ClassDefContext
from mypy.plugin import Plugin


_envier_base_classes = frozenset({"envier.En", "envier.Env"})


def _envier_base_class_callback(ctx: ClassDefContext) -> None:
    for stmt in ctx.cls.defs.body:
        if isinstance(stmt, ClassDef):
            # Check that we have an expected base class. If it also has an
            # __item__ attribute, we should create a field with that name in the
            # parent class.
            if {
                _.fullname for _ in stmt.base_type_exprs
            } & _envier_base_classes and "__item__" in stmt.info.names:
                for s in (_ for _ in stmt.defs.body if isinstance(_, AssignmentStmt)):
                    if "__item__" in {_.name for _ in s.lvalues}:
                        break
                else:
                    return

                # The value of the __item__ attribute must be a string.
                assert isinstance(s.rvalue, StrExpr), s.rvalue

                # An explicit annotation already provides a portable type for
                # the dynamically named nested configuration.
                if s.rvalue.value in ctx.cls.info.names:
                    continue

                # Move the statement over from the class name to the item name
                ctx.cls.info.names[s.rvalue.value] = ctx.cls.info.names.pop(stmt.name)


class EnvierPlugin(Plugin):
    def get_base_class_hook(
        self, fullname: str
    ) -> t.Optional[t.Callable[[ClassDefContext], None]]:
        if fullname in _envier_base_classes:
            # Preserve support for dynamically named nested configurations.
            return _envier_base_class_callback

        return None


def plugin(version: str) -> t.Type[EnvierPlugin]:
    return EnvierPlugin
