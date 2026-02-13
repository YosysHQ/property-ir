from hypothesis import strategies as st

from src.sexpr.base import RawSExprList



def identifier() -> st.SearchStrategy:
    #return st.text(min_size=1)
    return st.from_regex(r"[A-Za-z0-9-_]+", fullmatch=True)

identifier_list: st.SearchStrategy = st.lists(elements=identifier(), min_size=1, max_size=8, unique=True)

def raw_sexpr() -> st.SearchStrategy:
    return st.recursive(base=identifier(), extend=lambda children: st.lists(elements=children, min_size=1))


@st.composite
def bounded_range(draw) -> RawSExprList:
    lower = draw(st.integers(min_value=0))
    upper = draw(st.integers(min_value=lower))
    return ['bounded-range', str(lower), str(upper)]

@st.composite
def constant_range(draw) -> RawSExprList:
    lower = draw(st.integers(min_value=0))
    upper = draw(st.integers(min_value=lower) | st.just('$'))
    return ['range', str(lower), str(upper)]

def parsable_boolean(declared_signals: list[str]) -> st.SearchStrategy:
    base = st.one_of(
            st.sampled_from(declared_signals),
            st.sampled_from([['constant', 'true'],
                ['constant', 'false'],
                ['true'],
                ['false']]))
    return st.recursive(base=base, extend=lambda children:
            st.lists(children, min_size=1, max_size=4).map(lambda lst: ['and'] + lst) |
            st.lists(children, min_size=1, max_size=4).map(lambda lst: ['or'] + lst) |
            children.map(lambda elem: ['not', elem]),
            max_leaves=2
    )

def parsable_sequence(declared_signals: list[str]) -> st.SearchStrategy:
    base = parsable_boolean(declared_signals).map(lambda elem: ['seq-bool', elem])

    return st.recursive(base=base, extend=lambda children:
            st.lists(children, min_size=1, max_size=4).map(lambda lst: ['seq-concat'] + lst) |
            st.builds(lambda rng, seq: ['seq-repeat', rng, seq],  constant_range(), children),
            max_leaves=2
    )

def parsable_property(declared_signals: list[str]) -> st.SearchStrategy:
    base = parsable_sequence(declared_signals).map(lambda elem: ['prop-seq', elem])

    return st.recursive(base=base, extend=lambda children:
            children.map(lambda elem: ['prop-always', elem]) |
            st.builds(lambda rng, prop: ['prop-always-ranged', rng, prop], constant_range(), children) |
            st.builds(lambda seq, prop: ['prop-non-overlapped-implication', seq, prop], parsable_sequence(declared_signals), children) |
            st.lists(children, min_size=1, max_size=4).map(lambda lst: ['prop-and'] + lst),
            max_leaves=2)


def parsable_let_rec():
    pass

def parsable_declare_rec():
    pass


@st.composite
def parsable_boolean_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_boolean(declared_signals))
    return ['document',
        ['add-signals'] + declared_signals,
        ['parse-sexpr', expr]
    ]

@st.composite
def parsable_sequence_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_sequence(declared_signals))
    return ['document',
        ['add-signals'] + declared_signals,
        ['parse-sexpr', expr]
    ]

@st.composite
def parsable_property_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_property(declared_signals))
    return ['document',
        ['add-signals'] + declared_signals,
        ['parse-sexpr', expr]
    ]

@st.composite
def parsable_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_boolean(declared_signals) | parsable_sequence(declared_signals) | parsable_property(declared_signals))
    return ['document',
        ['add-signals'] + declared_signals,
        ['parse-sexpr', expr]
    ]



def main():

    print(identifier().example())
    print(raw_sexpr().example())
    print(bounded_range().example())
    print(constant_range().example())

    declared_signals = identifier_list.example()
    print(declared_signals)
    print(parsable_boolean(declared_signals).example())
    print(parsable_boolean_document().example())

    print(parsable_sequence(declared_signals).example())
    print(parsable_property(declared_signals).example())
    print(parsable_document().example())


if __name__ == "__main__":

    main()