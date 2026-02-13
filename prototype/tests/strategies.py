from hypothesis import strategies as st
#from hypothesis.strategies import composite



def identifier():
    #return st.text(min_size=1)
    #return st.text(st.characters(codec="ascii"), min_size=1)
    return st.from_regex(r"[A-Za-z0-9-_]+", fullmatch=True)

def raw_sexpr():
    return st.recursive(base=identifier(), extend=lambda children: st.lists(elements=children, min_size=1))


@st.composite
def bounded_range(draw):
    lower = draw(st.integers(min_value=0))
    upper = draw(st.integers(min_value=lower))
    return ['bounded-range', str(lower), str(upper)]

    #return st.builds(lambda lower, upper: ['bounded-range', str(lower), str(upper)],
    #    lower=st.integers(min_value=0), upper=st.integers(min_value=0))

@st.composite
def constant_range(draw):

    lower = draw(st.integers(min_value=0))
    upper = draw(st.integers(min_value=lower) | st.just('$'))
    return ['range', str(lower), str(upper)]

    #return st.builds(lambda lower, upper: ['range', str(lower), str(upper)],
    #    lower=st.integers(min_value=0), upper=st.integers(min_value=0) | st.just('$'))


def base_boolean():
    pass

def parsable_raw_sexpr_boolean():
    pass



def base_sequence():
    pass


def parsable_raw_sexpr_sequence():
    pass




def base_property():
    pass


def parsable_raw_sexpr_property():
    pass






def main():

    print(identifier().example())
    print(raw_sexpr().example())
    print(bounded_range().example())
    print(constant_range().example())
    #print(base_boolean().example())


if __name__ == "__main__":

    main()