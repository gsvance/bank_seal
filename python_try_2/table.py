"""Code for formatting tabular data as pretty multi-line strings.

Last modified 14 Oct 2023 by Greg Vance.
"""


from typing import Any, List


COLUMN_SEPARATOR = 2 * ' '
LINE_CHARACTER = '='


def format_as_table(
    columns: List[List[Any]],
    column_names: List[str],
    right_aligned: List[bool] | None = None
) -> str:
    """Format column data as a pretty multi-line table string.

    The elements of each column can be any data type that is convertable to
    str, though there should typically only be one data type per column. The
    column names will appear in the table header. The right_aligned parameter
    determines whether the data in each column will be left-aligned (False) or
    right-aligned (True), with the default being to left-align all columns.
    """
    if right_aligned is None:
        right_aligned = [False for _ in columns]

    n_columns_set = set(
        len(arg) for arg in [columns, column_names, right_aligned]
    )
    if len(n_columns_set) != 1:
        raise TypeError(f"inconsistent number of columns: {n_columns_set}")
    if n_columns_set == {0}:
        raise TypeError("cannot format a table with zero columns")

    n_rows_set = set(len(column) for column in columns)
    if len(n_rows_set) != 1:
        raise TypeError(f"mismatched column lengths in table: {n_rows_set}")

    column_widths = [
        max(len(entry) for entry in map(str, [name] + column))
        for column, name in zip(columns, column_names)
    ]

    header = COLUMN_SEPARATOR.join(
        (name.rjust(width) if align_right else name.ljust(width))
        for name, width, align_right
        in zip(column_names, column_widths, right_aligned)
    )

    table = [header, LINE_CHARACTER * len(header)]

    for row_data in zip(*columns):
        row_entries = map(str, row_data)
        row = [
            (entry.rjust(width) if align_right else entry.ljust(width))
            for entry, width, align_right
            in zip(row_entries, column_widths, right_aligned)
        ]
        table.append(COLUMN_SEPARATOR.join(row))

    return '\n'.join(table)
