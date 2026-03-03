from typing import Optional
from hypothesis import strategies as st
from hypothesis import settings
import logging

from src.sexpr.base import RawSExpr, RawSExprList
from tests.helpers import wrap_signals_and_expr_in_document


logger = logging.getLogger(__name__)


def identifier() -> st.SearchStrategy:
    #return st.text(min_size=1)
    return st.from_regex(r"[A-Za-z0-9-_]+", fullmatch=True)

identifier_list: st.SearchStrategy = st.lists(elements=identifier(), min_size=1, max_size=5, unique=True)

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
            max_leaves=4
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


@st.composite
def parsable_let_rec_boolean(draw, declared_signals: list[str]) -> RawSExprList:
    let_identifiers = draw(st.lists(elements=identifier().filter(lambda x: x not in declared_signals), min_size=1, max_size=3, unique=True))
    logger.debug('declared_signals %s', declared_signals)
    logger.debug('let_identifiers %s', let_identifiers)
    all_identifiers = declared_signals + let_identifiers
    let_rec_expr = []
    for idf in let_identifiers:
        expr: RawSExprList = draw(parsable_boolean(all_identifiers).filter(lambda x: x not in let_identifiers))
        let_rec_expr.append([idf, expr])
    return_value = draw(st.sampled_from(let_identifiers))
    return ['let-rec'] + let_rec_expr + [return_value] # type: ignore


@st.composite
def parsable_let_rec_boolean_nested(draw, declared_names: list[str], inner=False) -> RawSExprList:
    let_identifiers = draw(st.lists(elements=identifier().filter(lambda x: x not in declared_names), min_size=1, max_size=3, unique=True))
    all_identifiers = declared_names + let_identifiers
    inner_let_rec: Optional[RawSExprList] = None
    nested_idf: Optional[str] = None
    if not inner:
        inner_let_rec = draw(parsable_let_rec_boolean_nested(declared_names=all_identifiers, inner=True))
        nested_idf = draw(st.sampled_from(let_identifiers))
    let_rec_expr = []
    for idf in let_identifiers:
        if not inner:
            if idf == nested_idf:
                let_rec_expr.append([idf, inner_let_rec])
                continue
        expr: RawSExprList = draw(parsable_boolean(all_identifiers).filter(lambda x: x not in all_identifiers))
        let_rec_expr.append([idf, expr])
    return_value = draw(st.sampled_from(let_identifiers))
    return ['let-rec'] + let_rec_expr + [return_value] # type: ignore



def parsable_declare_rec():
    pass


@st.composite
def parsable_let_rec_boolean_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_let_rec_boolean(declared_signals))
    return wrap_signals_and_expr_in_document(declared_signals, expr)

@st.composite
def parsable_let_rec_boolean_nested_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_let_rec_boolean_nested(declared_signals))
    return wrap_signals_and_expr_in_document(declared_signals, expr)

@st.composite
def parsable_boolean_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_boolean(declared_signals))
    return wrap_signals_and_expr_in_document(declared_signals, expr)

@st.composite
def parsable_sequence_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_sequence(declared_signals))
    return wrap_signals_and_expr_in_document(declared_signals, expr)

@st.composite
def parsable_property_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_property(declared_signals))
    return wrap_signals_and_expr_in_document(declared_signals, expr)

@st.composite
def parsable_document(draw) -> RawSExprList:
    declared_signals = draw(identifier_list)
    expr = draw(parsable_boolean(declared_signals) | parsable_sequence(declared_signals) | parsable_property(declared_signals))
    return wrap_signals_and_expr_in_document(declared_signals, expr)



def main():

    logger.info(identifier().example())
    logger.info(raw_sexpr().example())
    logger.info(bounded_range().example())
    logger.info(constant_range().example())

    declared_signals = identifier_list.example()
    logger.info(declared_signals)
    logger.info(parsable_boolean(declared_signals).example())
    logger.info(parsable_boolean_document().example())

    logger.info(parsable_sequence(declared_signals).example())
    logger.info(parsable_property(declared_signals).example())
    logger.info(parsable_document().example())


if __name__ == "__main__":

    main()