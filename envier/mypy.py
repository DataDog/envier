import typing as t

from mypy import exprtotype
from mypy import types
from mypy.nodes import ARG_POS
from mypy.nodes import ARG_STAR
from mypy.nodes import ARG_STAR2
from mypy.nodes import AssignmentStmt
from mypy.nodes import CallExpr
from mypy.nodes import ClassDef
from mypy.nodes import IndexExpr
from mypy.nodes import MemberExpr
from mypy.nodes import NameExpr
from mypy.nodes import StrExpr
from mypy.nodes import TypeAlias
from mypy.nodes import TypeInfo
from mypy.nodes import Var
from mypy.plugin import ClassDefContext
from mypy.plugin import MethodContext
from mypy.plugin import Plugin
from mypy.typeops import make_simplified_union
from mypy.types import FunctionLike
from mypy.types import Instance
from mypy.types import RawExpressionType
from mypy.types import Type
from mypy.types import TypeType

# Field declaration helpers for environment and derived values.
_envier_attr_makers = frozenset({"v", "d", "var", "der"})

_envier_base_classes = frozenset({"envier.En", "envier.Env"})


def _envier_attr_callback(ctx: MethodContext) -> Type:
    """Infer the value type returned by a field declaration helper."""
    if not ctx.arg_types[0] or ctx.arg_kinds[0][0] in (ARG_STAR, ARG_STAR2):
        return ctx.default_return_type
    arg_type = types.get_proper_type(ctx.arg_types[0][0])
    if isinstance(arg_type, TypeType):
        return arg_type.item
    if isinstance(arg_type, Instance):
        # WARNING: This returns an UnboundType which seems to match whatever!
        try:
            result = exprtotype.expr_to_unanalyzed_type(ctx.args[0][0], ctx.api.options)
        except exprtotype.TypeTranslationError:
            return ctx.default_return_type
        return (
            ctx.default_return_type if isinstance(result, RawExpressionType) else result
        )

    if not isinstance(arg_type, FunctionLike):
        return ctx.default_return_type
    return make_simplified_union({_.ret_type for _ in arg_type.items})  # type: ignore[arg-type]


def _type_info(node: object) -> t.Optional[TypeInfo]:
    if isinstance(node, TypeAlias) and isinstance(node.target, Instance):
        node = node.target.type
    return node if isinstance(node, TypeInfo) else None


def _is_envier_maker(node: object, name: str) -> bool:
    info = _type_info(node)
    method = info.get(name) if info and name in _envier_attr_makers else None
    return method is not None and method.fullname == f"envier.env.Env.{name}"


def _envier_base_class_callback(
    ctx: ClassDefContext, rewrite_nested: bool = True
) -> None:
    """Assign declared value types to fields created by var, v, der, or d."""
    for stmt in ctx.cls.defs.body:
        if isinstance(stmt, AssignmentStmt):
            decl = stmt.rvalue
            if (
                len(stmt.lvalues) != 1
                or not isinstance(decl, CallExpr)
                or not isinstance(decl.callee, MemberExpr)
            ):
                # We assume a single assignment per line, so this can't be an
                # envier attribute maker.
                continue

            owner = decl.callee.expr
            if isinstance(owner, IndexExpr):
                owner = owner.base
            if not isinstance(owner, (NameExpr, MemberExpr)) or not _is_envier_maker(
                owner.node, decl.callee.name
            ):
                continue

            if "type" in decl.arg_names:
                type_arg = decl.args[decl.arg_names.index("type")]
            elif decl.args and decl.arg_kinds[0] == ARG_POS:
                type_arg = decl.args[0]
            else:
                continue

            if isinstance(type_arg, (NameExpr, MemberExpr)) and isinstance(
                type_arg.node, Var
            ):
                # Runtime type values are handled by the method callback.
                continue

            (attr,) = stmt.lvalues
            if not isinstance(attr, NameExpr) or not isinstance(attr.node, Var):
                continue

            try:
                unanalyzed_type = exprtotype.expr_to_unanalyzed_type(
                    type_arg, ctx.api.options
                )
            except exprtotype.TypeTranslationError:
                continue
            field_type = ctx.api.anal_type(unanalyzed_type)
            if field_type is None:
                continue
            attr.node.type = field_type

            attr.is_inferred_def = False

        elif rewrite_nested and isinstance(stmt, ClassDef):
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
        if symbol is not None and _is_envier_maker(symbol.node, name):
            # We use this callback to override the the method return value to
            # match the attribute value, which is also inferred by the `type`
            # argument.
            return _envier_attr_callback

        return None

    def get_base_class_hook(
        self, fullname: str
    ) -> t.Optional[t.Callable[[ClassDefContext], None]]:
        if fullname in _envier_base_classes:
            return _envier_base_class_callback

        symbol = self.lookup_fully_qualified(fullname)
        info = _type_info(symbol.node if symbol is not None else None)
        if info is not None and info.has_base("envier.env.Env"):
            # Indirect subclasses need field types, without reapplying the
            # existing nested-class rewrite for every base or semantic pass.
            return lambda ctx: _envier_base_class_callback(ctx, rewrite_nested=False)

        return None


def plugin(version: str) -> t.Type[EnvierPlugin]:
    return EnvierPlugin
