"""Handles pretty I/O of integers using commas as digit separators.

Last modified 9 Feb 2023 by Greg Vance.
"""


import re


# This regex lays out the *proper* format of a comma-separated integer
COMMA_INT_FORMAT_REGEX = re.compile(r"""
    \A\s*            # Optional leading whitespace
    (?P<sign>[-+]?)  # Possible sign
    (?P<body>        # The body of the integer is either
        \d+          # an uninterrupted string of one or more digits
    |                # or
        \d{1,3}      # a string of one to three digits followed by
        (?:,\d{3})+  # one or more comma-separated triples of digits
    )
    \s*\Z            # Optional trailing whitespace
""", re.VERBOSE)

# This regex specifies exactly where to position commas in a string of digits
# to create a properly formatted comma-separated integer
COMMA_POSITION_REGEX = re.compile(r"""
    (?<=\d)           # Always place a comma after a digit
    (?=(?:\d{3})+\Z)  # and before one or more digit triplets
""", re.VERBOSE)


def parse_comma_int(string: str) -> int:
    """Parse an integer value from a string that may include commas.

    The string may optionally include commas if used correctly as digit
    separators. For example, the input "23,009,108" produces the int 23009108.
    If commas *are* included in the string, then their usage *must* be correct,
    meaning that they must delimit *every* set of three digits starting from
    the rightmost. Incorrect placement signals a possible typo, and this
    function will therefore raise an exception. The use of leading zeros will
    also raise an exception unless the leading zero is the only digit present,
    i.e., the input represents the integer 0 itself.
    """
    regex_match = COMMA_INT_FORMAT_REGEX.fullmatch(string)

    # Pedantically insist that commas are positioned correctly when included
    # Incorrect positioning of commas could indicate that the user made a typo
    if not regex_match:
        raise ValueError(f"failed to parse comma-separated int: {string!r}")

    body_without_commas = regex_match.group("body").replace(",", "")

    # While we're being pedantic, also forbid any sort of leading zeros
    if body_without_commas != "0" and body_without_commas.startswith('0'):
        raise ValueError("won't parse comma-separated int with leading zero")

    return int(regex_match.group("sign") + body_without_commas)


def render_comma_int(integer: int) -> str:
    """Render an integer value to a string with commas inserted as needed.

    Zero or more commas will be inserted as digit separators every set of three
    digits from the right. For example, an input value of 23009108 produces the
    str "23,009,108". This is intended as a pretty-printing function for
    improved readability of large integers, but also demonstrates the correct
    input format required by the parse_comma_int() function.
    """
    return COMMA_POSITION_REGEX.sub(",", str(integer))
