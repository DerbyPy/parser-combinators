"""Parser combinators in Python.

The goal is to write your parser just like you would write your grammar[1].

At the end it is very readable and maintainable, not to mention it actually works.

This approach is inspired by the Haskell library Parsec[2] which does a much better job at it.

For a Python library that does this well, check out pyparsing[3].

[1] https://en.wikipedia.org/wiki/Formal_grammar
[2] https://wiki.haskell.org/Parsec
[3] https://pyparsing.wikispaces.com/
"""

from collections import namedtuple
from functools import reduce

# State is a type which captures the "state" of a parse. In other words, it is how a parser
# remembers what it has finished and what is left to parse.
# The State type is just a tuple with two elements.
#   * `value` is the *result* of the parse, so far.
#   * `remaining` is the portion of the input that has yet to be parsed.
State = namedtuple('State', ['value', 'remaining'])


def identity(x):
    """A function that simply returns its input unchanged.

    When treated as a parser, `identity` is a parser that always succeeds and has no effect on the
    state (in other words, it does not consume any input and it does not add any new data to
    the value).
    """
    return x


def compose(functions):
    """Function composition[1]

    Think unix pipes, but from right-to-left instead of left-to-right.

    [1] https://en.wikipedia.org/wiki/Function_composition
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, identity)


class ParseFail(Exception):
    """An exception for parse failures.

    The exception remembers what the state was when the parse failed and what the parser was
    expecting.
    """
    def __init__(self, state, expected):
        self.state = state
        self.expected = expected

    def __str__(self):
        return 'Expected ' + self.expected


def char_satisfies(pred, name):
    """Returns a new parser for a single character.

    See uses for examples.

    :param pred: is a "predicate" function which looks at a single character and returns True
                 if it should be considered valid or false otherwise.
    :param name: is some "name" to give to this kind of character.
    """
    def parser(state):
        if len(state.remaining) > 0 and pred(state.remaining[0]):
            return State(state.value + [state.remaining[0]], state.remaining[1:])
        raise ParseFail(state, expected=name)
    return parser


def pure(x):
    """A parser which simply inserts a new value into the parse result, but does not consume any
    input."""
    def parser(state):
        return State(state.value + [x], state.remaining)
    return parser


def char(x):
    """Returns a parser that only accepts an exact match on a character.

    For example, `char('A')` returns a parser thta only accepts the letter 'A' or it fails.

    :param x: is the character to accept.
    """
    return char_satisfies(lambda c: c == x, 'character "{}"'.format(x))

# A parser that accepts any single character. It's like "." in regex.
any_char = char_satisfies(lambda _: True, 'any character')


def one_of(chars):
    """Returns a parser that accepts any of the given chars, but no others. It's like "[abc]"
    in regex.

    For example, `one_of(['a', 'b', 'c'])` will accept, "a", or "b", or "c", but that's it.

    :param chars: is an iterable of characters to accept.
    """
    return char_satisfies(lambda c: c in chars, 'one of ' + ','.join(chars))


def none_of(chars):
    """Returns a parser that accepts any character except the ones given. It's like "[^abc]" in
    regex.

    This is the opposie of the `one_of` parser.

    :param chars: is an iterable of characters to reject.
    """
    return char_satisfies(lambda c: c not in chars, 'none of ' + ','.join(chars))


def sequence(parsers):
    """Function composition backwards, i.e. in the order that makes more sense in our context."""
    return compose(reversed(parsers))


def many(parser):
    """Returns a parser that runs the given parser as many times as it can until it fails. This is
    like "*" in regex. The technical term is Kleene star.

    :param parser: is the parser to run many times. For example, `many(any_char)` is equivalent to
                   the regex ".*".
    """
    def new_parser(state):
        while True:
            try:
                state = parser(state)
            except ParseFail:
                return state
    return new_parser


def many1(parser):
    """Like `many` but requires at least one occurrence. This is like "+" in regex."""
    return sequence([parser, many(parser)])


def choose(parsers):
    """Returns a parser that tries the given parsers in order and uses the first one that succeeds.
    This is like "(a|b|c)" in regex.

    :param parsers: is an iterable of parsers to choose from.
    """
    def new_parser(state):
        for parser in parsers[:-1]:
            try:
                return parser(state)
            except ParseFail:
                pass
        return parsers[-1](state)
    return new_parser


def maybe(parser):
    """Returns a parser that allows the given parser to fail silently. This is like "?" in regex.

    For example, `maybe(char('a'))` will accept both "ab" and "b" (without the "a") since the "a" is
    optional.

    :param parser: is the parser that can fail.
    """
    return choose([parser, identity])


def eof(state):
    """A parser that accepts the EOF (end of file) or fails otherwise. This is like "$" in regex.
    """
    if state.remaining == '':
        return state
    raise ParseFail(state, expected='the end')


def coerce(coercion, parser):
    """Returns a parser that runs the given parser and coerces its result with the given coercion.

    :param coercion: is some function which coerces the result value to something else.
    :param parser: the parser whose result we wish to coerce.
    """
    def new_parser(state):
        new_state = parser(State([], state.remaining))
        return State(state.value + [coercion(new_state.value)], new_state.remaining)
    return new_parser


def text(parser):
    """Returns a parser that runs the given parser and turns its result value into a string."""
    return coerce(''.join, parser)


def as_int(parser):
    return coerce(compose([int, ''.join]), parser)


def as_tuple(parser):
    """Coerces parser result to a tuple."""
    return coerce(tuple, parser)


def as_list(parser):
    """Coerces parser result to a list."""
    return coerce(list, parser)


def discard(parser):
    """Returns a parser that runs the given parser and throws away its result value."""
    def new_parser(state):
        new_state = parser(state)
        return State(state.value, new_state.remaining)
    return new_parser


# A parser that accepts an alphabetic character.
letter = char_satisfies(str.isalpha, 'letter')

# A parser that accepts a numeric digit.
digit = char_satisfies(str.isdigit, 'digit')

# A parser that accepts some number of letters and then turns them into a string.
word = text(many1(letter))

# A parser that accepts an integer and then turns it into an int.
integer = as_int(sequence([choose([char('-'), char('+'), identity]), many1(digit)]))

# A parser that accepts a whitespace character.
whitespace = char_satisfies(str.isspace, 'whitespace')


def token(parser):
    """Returns a parser that skips whitespace before and after the given parser."""
    skip_ws = discard(many(whitespace))
    return sequence([skip_ws, parser, skip_ws])


def between(left, right, middle):
    """Returns a parser that accepts a parser between two others.

    See uses for examples.

    :param left: is a parser to run on the left.
    :param right: is a parser to run on the right.
    :param middle: is a parser to run in the middle.
    """
    return token(sequence([discard(left), middle, discard(right)]))


def double_quoted(parser):
    """Returns a parser which accepts the given parser between double quotes."""
    return between(char('"'), char('"'), parser)


def sep_by1(separator, parser):
    """Returns a parser that accepts the given parser, separated by another. This requires at least
    one occurrence. This discards the separator.

    For example, `sep_by1(char(','), digit)` would accept '1,2,3'.

    :param separator: the parser that runs in between each occurrence of `parser`.
    :param parser: the parser for each occurrence.
    """
    return sequence([parser, many(sequence([discard(separator), parser]))])


def sep_by(separator, parser):
    """Like sep_by1 but allows for zero occurrences."""
    return maybe(sep_by1(separator, parser))


# --------------------------------------------------------------------------------------------------
# Primitive JSON parser
# --------------------------------------------------------------------------------------------------

# A JSON string, which is double-quoted. This does not handle escaping.
string = double_quoted(text(many(none_of(['"']))))

key = string


class FunctionWrapper(object):
    """A class that acts just like a function, but lets us mutate the function underneath.
    This is a hack necessary to define mutually recursive parsers in Python, since Python does not
    let you use variables before you define them."""
    def __init__(self, impl=None):
        self.impl = impl

    def __call__(self, *args, **kwargs):
        return self.impl(*args, **kwargs)


# A placeholder for our dict_ parser. We need to do this because the definition of dict_ refers to
# itself, so we need to start with a placeholder and then mutate it later to fill it in.
dict_ = FunctionWrapper()


# Any of the JSON values that we accept (we don't accept the full JSON spec, for example,
# lists are missing right now.)
value = choose([string, integer, dict_])

# A key-value pair, separated by a colon.
key_value = as_tuple(sequence([text(token(key)), discard(char(':')), token(value)]))

# Now that we've defined the inner guts of the dict_ parser (which themselves refer to the dict_
# parser), we can fill in the dict_ parser to what it should be.
dict_.impl = as_list(between(char('{'), char('}'), sep_by(token(char(',')), key_value)))


if __name__ == '__main__':
    test = '{"outer key": 9, "nested key": {"inside": "cold in here"}}'
    print('Example: Parse', test)

    result = value(State([], '{"outer key": 9, "nested key": {"inside": "cold in here"}}'))
    print(result)
