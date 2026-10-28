import typing as t

from mypy import exprtotype
from mypy import types
from mypy.nodes import ARG_POS
from mypy.nodes import ARG_STAR
from mypy.nodes import ARG_STAR2
from mypy.nodes import AssignmentStmt
from mypy.nodes import CallExpr
from mypy.nodes import ClassDef
from mypy.nodes import Decorator
from mypy.nodes import FuncDef
from mypy.nodes import MemberExpr
from mypy.nodes import NameExpr
from mypy.nodes import OverloadedFuncDef
from mypy.nodes import StrExpr
from mypy.nodes import TypeAlias
from mypy.nodes import TypeInfo
from mypy.nodes import TypeVarLikeExpr
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

_envier_base_classes = frozenset({"envier.En", "envier.Env", "envier.env.Env"})


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


def _is_envier_class(fullname: str, node: object) -> bool:
    """Recognize Env aliases and subclasses that expose declaration helpers."""
    if isinstance(node, TypeAlias) and isinstance(node.target, Instance):
        node = node.target.type
    return fullname in _envier_base_classes or (
        isinstance(node, TypeInfo)
        and (node.fullname == "envier.env.Env" or node.has_base("envier.env.Env"))
    )


def _is_envier_maker(node: object, name: str) -> bool:
    """Check that a method is Env's var, v, der, or d declaration helper."""
    if isinstance(node, TypeAlias) and isinstance(node.target, Instance):
        node = node.target.type
    if not isinstance(node, TypeInfo) or name not in _envier_attr_makers:
        return False
    method = node.get(name)
    return (
        method is not None
        and method.node is not None
        and method.node.fullname == f"envier.env.Env.{name}"
    )


def _rename_nested_type(node: object, old: str, new: str) -> None:
    """Keep serialized names consistent with the nested configuration's name."""
    if isinstance(node, Decorator):
        _rename_nested_type(node.func, old, new)
        _rename_nested_type(node.var, old, new)
    elif isinstance(
        node, (TypeInfo, Var, FuncDef, OverloadedFuncDef, TypeAlias, TypeVarLikeExpr)
    ):
        if node.fullname != old and not node.fullname.startswith(old + "."):
            return
        node._fullname = node.fullname.replace(old, new, 1)
        if isinstance(node, TypeInfo):
            node.defn.fullname = node.fullname
            for symbol in node.names.values():
                _rename_nested_type(symbol.node, old, new)
        elif isinstance(node, OverloadedFuncDef):
            for item in node.items:
                _rename_nested_type(item, old, new)
            _rename_nested_type(node.impl, old, new)


def _envier_base_class_callback(ctx: ClassDefContext) -> None:
    """Assign declared value types to fields created by var, v, der, or d."""
    # Renaming siblings before deferred nested classes are ready can corrupt
    # their symbols when semantic analysis revisits the class body.
    if any(isinstance(stmt, ClassDef) and not stmt.info for stmt in ctx.cls.defs.body):
        return
    for stmt in ctx.cls.defs.body:
        if isinstance(stmt, AssignmentStmt):
            decl = stmt.rvalue
            if (
                len(stmt.lvalues) != 1
                or not isinstance(decl, CallExpr)
                or not isinstance(decl.callee, MemberExpr)
                or not isinstance(decl.callee.expr, (NameExpr, MemberExpr))
                or not _is_envier_maker(decl.callee.expr.node, decl.callee.name)
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

        elif isinstance(stmt, ClassDef):
            # Check that we have an expected base class. If it also has an
            # __item__ attribute, we should create a field with that name in the
            # parent class.
            if stmt.info.has_base("envier.env.Env") and "__item__" in stmt.info.names:
                for s in (_ for _ in stmt.defs.body if isinstance(_, AssignmentStmt)):
                    if any(
                        isinstance(_, NameExpr) and _.name == "__item__"
                        for _ in s.lvalues
                    ):
                        break
                else:
                    continue

                # The value of the __item__ attribute must be a string.
                if not isinstance(s.rvalue, StrExpr):
                    continue

                # Move the statement over from the class name to the item name
                symbol = ctx.cls.info.names.get(stmt.name)
                if symbol is not None and symbol.node is stmt.info:
                    _rename_nested_type(
                        stmt.info,
                        stmt.info.fullname,
                        f"{ctx.cls.info.fullname}.{s.rvalue.value}",
                    )
                    ctx.cls.info.names[s.rvalue.value] = ctx.cls.info.names.pop(
                        stmt.name
                    )


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
        symbol = self.lookup_fully_qualified(fullname)
        if _is_envier_class(fullname, symbol.node if symbol is not None else None):
            # We use this callback to override the class attribute types to
            # match the ones declared by the `type` argument of the Env methods.
            return _envier_base_class_callback

        return None


def plugin(version: str) -> t.Type[EnvierPlugin]:
    return EnvierPlugin
