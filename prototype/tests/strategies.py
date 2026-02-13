from hypothesis import strategies as st

from sexpr import RawSExprList



def identifier():
    #return st.text(min_size=1)
    return st.from_regex(r"[A-Za-z0-9-_]+", fullmatch=True)

identifier_list = st.lists(elements=identifier(), min_size=1, max_size=20, unique=True)

def raw_sexpr():
    return st.recursive(base=identifier(), extend=lambda children: st.lists(elements=children, min_size=1))


@st.composite
def bounded_range(draw):
    lower = draw(st.integers(min_value=0))
    upper = draw(st.integers(min_value=lower))
    return ['bounded-range', str(lower), str(upper)]

@st.composite
def constant_range(draw):
    lower = draw(st.integers(min_value=0))
    upper = draw(st.integers(min_value=lower) | st.just('$'))
    return ['range', str(lower), str(upper)]


def parsable_boolean(declared_signals: list[str]):
    base = st.one_of(
            st.sampled_from(declared_signals),
            st.sampled_from([['constant', 'true'],
                ['constant', 'false'],
                ['true'],
                ['false']]))
    return st.recursive(base=base, extend=lambda children:
        st.lists(children, min_size=1).map(lambda lst: ['and'] + lst) |
        st.lists(children, min_size=1).map(lambda lst: ['or'] + lst) |
        children.map(lambda elem: ['not', elem])
    )



def base_sequence():
    pass


def parsable_sequence():
    pass




def base_property():
    pass


def parsable_property():
    pass

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



def main():

    print(identifier().example())
    print(raw_sexpr().example())
    print(bounded_range().example())
    print(constant_range().example())

    declared_signals = identifier_list.example()
    print(declared_signals)
    print(parsable_boolean(declared_signals).example())
    print(parsable_boolean_document().example())


if __name__ == "__main__":

    main()