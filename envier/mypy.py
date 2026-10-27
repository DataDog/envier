import typing as t

from mypy.exprtotype import expr_to_unanalyzed_type
from mypy.nodes import ARG_POS
from mypy.nodes import AssignmentStmt
from mypy.nodes import CallExpr
from mypy.nodes import ClassDef
from mypy.nodes import MemberExpr
from mypy.nodes import NameExpr
from mypy.nodes import StrExpr
from mypy.nodes import TypeInfo
from mypy.nodes import Var
from mypy.plugin import ClassDefContext
from mypy.plugin import MethodContext
from mypy.plugin import Plugin
from mypy.typeops import make_simplified_union
from mypy.types import FunctionLike
from mypy.types import Instance
from mypy.types import ProperType
from mypy.types import Type

_envier_attr_makers = frozenset({"v", "d", "var", "der"})

_envier_base_classes = frozenset({"envier.En", "envier.Env"})


def _envier_attr_callback(ctx: MethodContext) -> ProperType:
    arg_type = ctx.arg_types[0][0]
    if isinstance(arg_type, Instance):
        # WARNING: This returns an UnboundType which seems to match whatever!
        return expr_to_unanalyzed_type(ctx.args[0][0], ctx.api.options)

    assert isinstance(arg_type, FunctionLike), arg_type
    return make_simplified_union({_.ret_type for _ in arg_type.items})  # type: ignore[arg-type]


def _is_envier_class(fullname: str, node: object) -> bool:
    return fullname in _envier_base_classes or (
        isinstance(node, TypeInfo)
        and (node.fullname == "envier.env.Env" or node.has_base("envier.env.Env"))
    )


def _envier_base_class_callback(ctx: ClassDefContext) -> None:
    for stmt in ctx.cls.defs.body:
        if isinstance(stmt, AssignmentStmt):
            decl = stmt.rvalue
            if (
                len(stmt.lvalues) != 1
                or not isinstance(decl, CallExpr)
                or not isinstance(decl.callee, MemberExpr)
                or decl.callee.name not in _envier_attr_makers
                or not isinstance(decl.callee.expr, (NameExpr, MemberExpr))
                or not _is_envier_class(
                    decl.callee.expr.fullname, decl.callee.expr.node
                )
            ):
                # We assume a single assignment per line, so this can't be an
                # envier attribute maker.
                continue

            if "type" in decl.arg_names:
                type_arg = decl.args[decl.arg_names.index("type")]
            elif decl.args and decl.arg_kinds[0] == ARG_POS:
                type_arg = decl.args[0]
            else:
                continue

            (attr,) = stmt.lvalues
            assert isinstance(attr, NameExpr) and isinstance(attr.node, Var), attr

            attr.node.type = ctx.api.anal_type(
                expr_to_unanalyzed_type(type_arg, ctx.api.options)
            )

            attr.is_inferred_def = False

        elif isinstance(stmt, ClassDef):
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

                # Move the statement over from the class name to the item name
                ctx.cls.info.names[s.rvalue.value] = ctx.cls.info.names.pop(stmt.name)


class EnvierPlugin(Plugin):
    def get_method_hook(
        self, fullname: str
    ) -> t.Optional[t.Callable[[MethodContext], Type]]:
        owner, _, name = fullname.rpartition(".")
        if name not in _envier_attr_makers:
            return None

        symbol = self.lookup_fully_qualified(owner)
        if symbol is not None and _is_envier_class(owner, symbol.node):
            # We use this callback to override the the method return value to
            # match the attribute value, which is also inferred by the `type`
            # argument.
            return _envier_attr_callback

        return None

    def get_base_class_hook(
        self, fullname: str
    ) -> t.Optional[t.Callable[[ClassDefContext], None]]:
        symbol = self.lookup_fully_qualified(fullname)
        if _is_envier_class(fullname, symbol.node if symbol is not None else None):
            # We use this callback to override the class attribute types to
            # match the ones declared by the `type` argument of the Env methods.
            return _envier_base_class_callback

        return None


def plugin(version: str) -> t.Type[EnvierPlugin]:
    return EnvierPlugin
