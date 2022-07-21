import sys

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Directive
from docutils.parsers.rst import Parser
from docutils.utils import new_document


def asbool(argument):
    return argument.lower() in {"yes", "true", "t", "1", "y", "on"}


RST_PARSER = Parser()
RST_PARSER_SETTINGS = OptionParser(components=(Parser,)).get_default_values()


def _parse(cell):
    doc = new_document("", RST_PARSER_SETTINGS)
    RST_PARSER.parse(cell, doc)
    return doc.children


def _create_row(cells):
    row = nodes.row()
    for cell in cells:
        entry = nodes.entry()
        entry += _parse(cell)
        row += entry
    return row


class Envier(Directive):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "heading": asbool,
        "recursive": asbool,
    }

    def run(self):
        module_name, _, config_class = self.arguments[0].partition(":")
        __import__(module_name)
        module = sys.modules[module_name]

        config_spec = None
        for part in config_class.split("."):
            config_spec = getattr(module, part)
        if config_spec is None:
            raise ValueError(
                "Could not find configuration spec class {} from {}".format(
                    config_class, module_name
                )
            )

        has_header = self.options.get("heading", True)
        recursive = self.options.get("recursive", False)

        table = nodes.table()
        table["classes"] += ["colwidths-given"]

        # Column specs
        tgroup = nodes.tgroup(cols=4)
        table += tgroup
        for col_width in (3, 1, 1, 4):  # TODO: make it configurable?
            tgroup += nodes.colspec(colwidth=col_width)

        head = ("Variable Name", "Type", "Default Value", "Description")

        # Table heading
        if has_header:
            thead = nodes.thead()
            thead += _create_row(head)
            tgroup += thead

        # Table body
        tbody = nodes.tbody()
        tgroup += tbody
        for row in config_spec.help_info(recursive=recursive):
            tbody += _create_row(row)

        return [table]


def setup(app):
    app.add_directive("envier", Envier)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
