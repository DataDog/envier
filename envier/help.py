from textwrap import wrap
import typing as t


class RstListTable(object):
    HEADER = """.. list-table::
    :widths: {}
    :header-rows: 1

    * - Variable Name
      - Type
      - Default value
      - Description
"""

    ROW = """
        .. {}
    * - ``{}``
      - {}
      - {}
      - {}
"""

    def __init__(self, width=80, widths=(3, 1, 1, 4), header=True):
        # type: (int, t.Tuple[int, int, int, int], bool) -> None
        self.table = (
            self.HEADER.format(" ".join((str(w) for w in widths))) if header else ""
        )
        self.width = width

    def add_row(self, name, type, description, default=None):
        # type: (str, str, str, str) -> None
        """Add a list row to the table."""
        wrapped_lines = wrap(description, width=self.width - 8) if description else []
        if len(wrapped_lines) > 1:
            wrapped_lines[1:] = [" " * 8 + line for line in wrapped_lines[1:]]

        self.table += self.ROW.format(
            name.lower().replace("_", "-"),
            name,
            type,
            default or "",
            "\n".join(wrapped_lines),
        )

    def __str__(self):
        return self.table

    __repr__ = __str__
