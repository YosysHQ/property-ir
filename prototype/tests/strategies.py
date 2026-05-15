from typing import Optional, Callable, get_origin, get_args, Any
from collections import defaultdict
from hypothesis import strategies as st
from hypothesis import settings
import logging
import string

from sexpr.base import RawSExpr, RawSExprList, PropertyIrNode, IrContainer
from sexpr.base import Property, Sequence, Bool, Range, BoundedRange, IntOrUnbounded, Signal
from sexpr.parsing import parse_document, parse_raw_sexpr
import sexpr.primitives
from tests.helpers import wrap_signals_and_expr_in_document


logger = logging.getLogger(__name__)


# (primitive_name, primitive_type, signature, random_numbers_to_choose_argument)
type IrGeneratingType = tuple[str, type[PropertyIrNode], list[type], list[int]]

def random_ir(
    final_node_type: type[PropertyIrNode],
    primitive_filter: Callable[[type[PropertyIrNode]], bool] = lambda node_type: True,
    **lists_params) -> st.SearchStrategy[str]:
    """Generate a random Property IR expression whose graph has the form of a DAG.
    For this, collect all strategies to generate data for each allowed primitive.
    The primitive_filter can be used to include certain node types.
    The final_node_type is the type of the root."""

    primitive_generators = []
    final_primitive_generators = []
    allowed_types = [Property, Sequence, Bool]

    for node_type in allowed_types:
        for cls in node_type.__subclasses__():
            if primitive_filter(cls) and not cls is Signal:
                sub_strategy = random_ir_primitive_template_and_args(cls)
                primitive_generators.append(sub_strategy)
                if issubclass(cls, final_node_type):
                    final_primitive_generators.append(sub_strategy)

    return st.tuples(
        st.lists(st.one_of(primitive_generators), **lists_params),
        st.one_of(final_primitive_generators),
        identifier_list).map(build_ir_from_random_data)


def random_ir_primitive_template_and_args(node_class: type[PropertyIrNode]) -> st.SearchStrategy[IrGeneratingType]:
    """Given a type of PropertyIrNode, returns a strategy to get a tuple that can
    be used to generate one line of a let-rec for a random Property IR expression,
    corresponding to one node."""

    primitive_name: str = node_class.op_symbol()
    node_type: type[PropertyIrNode] = node_class.type_class()
    primitive_class_signature: list[type] = node_class.signature()

    min_s: int = len(primitive_class_signature)
    max_s: int = len(primitive_class_signature)

    if len(primitive_class_signature) == 1:
        if get_origin(primitive_class_signature[0]) is list:
            min_s: int = 2
            max_s: int = 5

    return st.tuples(st.just(primitive_name), st.just(node_type), st.just(primitive_class_signature), st.lists(st.integers(), min_size=min_s, max_size=max_s))


def build_ir_from_random_data(strategy_drawn_data: tuple[list[IrGeneratingType], IrGeneratingType, list[str]]) -> str:
    """Construct one Property IR document with a large let-rec generated from the
    given random data. The return value of the let-rec is represented by the second
    element of the given tuple. Each element in the list (the first element of the tuple)
    becomes one line."""

    generating_list: list[IrGeneratingType] = strategy_drawn_data[0] + [strategy_drawn_data[1]]

    logger.debug('generating_list: %s', generating_list)

    tuple_index_by_type: defaultdict[type[PropertyIrNode], list[str]] = defaultdict(list) # store for each node type the tuple index identifiers with that type
    unused_tuple_index_by_type: defaultdict[type[PropertyIrNode], list[str]] = defaultdict(list) # unused preceding nodes should be chosen with a higher probability

    signal_list: list[str] = strategy_drawn_data[2] # the signal identifiers cannot overlap with other node identifiers because they have max 3 letters

    let_rec_subexpressions: list[str] = []

    for tuple_num, (primitive_name, primitive_type, signature, random_numbers) in enumerate(generating_list):

        arguments: list[str] = []

        logger.debug('Processing tuple %s, %s, %s, %s', primitive_name, primitive_type, signature, random_numbers)

        for arg_num, random_num in enumerate(random_numbers):

            if get_origin(signature[0]) is list: # signature cannot be empty because there are > 0 random numbers
                arg_type: type = get_args(signature[0])[0]
            else:
                arg_type: type = signature[arg_num]

            # collect earlier list elements with correct type
            # and default values for type, if applicable
            candidates_unused_preceding_nodes: list[Any] = []
            candidates_preceding_nodes: list[Any] = []
            candidates_default: list[Any] = []
            candidates: list[Any] = []

            if issubclass(arg_type, Range) or issubclass(arg_type, BoundedRange):
                range_bounds = []
                range_bounds.append((random_num % 5) + 1) # add 1 because empty matches are not allowed
                range_bounds.append((random_num % 7) + 1)
                range_bounds.append((random_num % 13) + 1)
                if issubclass(arg_type, BoundedRange):
                    candidates.append(f'(bounded-range {min(range_bounds) } {max(range_bounds)})')
                elif issubclass(arg_type, Range):
                    candidates.append(f'(range {min(range_bounds) } {max(range_bounds)})')
                    candidates.append(f'(range {min(range_bounds) } $)')

            elif arg_type is int:
                candidates.append(str(random_num % 5))
                candidates.append(str(random_num % 7))
                candidates.append(str(random_num % 13))

            elif arg_type is bool:
                candidates = ['true', 'false']

            elif issubclass(arg_type, PropertyIrNode):

                candidates_preceding_nodes += tuple_index_by_type[arg_type]
                candidates_unused_preceding_nodes += unused_tuple_index_by_type[arg_type]
                logger.debug('candidates_preceding_nodes: %s', candidates_preceding_nodes)
                logger.debug('candidates_unused_preceding_nodes: %s', candidates_unused_preceding_nodes)
                logger.debug('tuple_index_by_type[arg_type]: %s', tuple_index_by_type)

                if issubclass(arg_type, Bool):
                    candidates_default += ['(true)', '(false)']
                    candidates_default += signal_list

                elif issubclass(arg_type, Sequence):
                    candidates_default += [f'(seq-bool {signal})' for signal in signal_list]

                elif issubclass(arg_type, Property):
                    candidates_default += [f'(prop-weak-bool {signal})' for signal in signal_list]
                    candidates_default += [f'(prop-strong-bool {signal})' for signal in signal_list]

                # choose candidates to select an argument from (prefer unused nodes over used ones and default values)
                if random_num % 10 in range(0, 9) and len(candidates_unused_preceding_nodes) > 0:
                    candidates = candidates_unused_preceding_nodes
                else:
                    candidates = candidates_preceding_nodes
                    candidates += candidates_default

            else:
                raise TypeError(f'Unexpected argument type {arg_type} while building expression for primitive {primitive_name}')

            # pick a candidate using the random int corresponding to that argument
            chosen_element: str = candidates[random_num % len(candidates)]
            arguments.append(chosen_element)

            if issubclass(arg_type, PropertyIrNode):
                if chosen_element in unused_tuple_index_by_type[arg_type]:
                    unused_tuple_index_by_type[arg_type].remove(chosen_element)

        # create string expression for the node
        primitive_str: str = f'(step{tuple_num} ({primitive_name} {" ".join(arguments)}))'
        let_rec_subexpressions.append(primitive_str)

        tuple_index_by_type[primitive_type].append(f'step{tuple_num}')
        unused_tuple_index_by_type[primitive_type].append(f'step{tuple_num}')
        logger.debug('Add step%s for primitive type %s', tuple_num, primitive_type)

    signals_str: str = " ".join([f"(declare-input {signal})" for signal in signal_list])
    subexpressions_str: str = " ".join(let_rec_subexpressions)

    return f'(document {signals_str} (parse-sexpr (let-rec {subexpressions_str} step{len(generating_list) - 1})))'





def identifier() -> st.SearchStrategy:
    return st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=3)

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
    for (i, idf) in enumerate(let_identifiers):
        expr: RawSExprList = draw(parsable_boolean(all_identifiers).filter(lambda x: x not in (let_identifiers+[None])[i:-1]))
        let_rec_expr.append([idf, expr])
    permuted_let_rec_expr = draw(st.permutations(let_rec_expr))
    return_value = draw(st.sampled_from(let_identifiers))
    return ['let-rec'] + permuted_let_rec_expr + [return_value] # type: ignore


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
    for (i, idf) in enumerate(let_identifiers):
        if not inner:
            if idf == nested_idf:
                let_rec_expr.append([idf, inner_let_rec])
                continue
        if inner:
            expr: RawSExprList = draw(parsable_boolean(all_identifiers).filter(lambda x: x not in declared_names and x not in (let_identifiers+[None])[i:-1]))
        else:
            expr: RawSExprList = draw(parsable_boolean(all_identifiers).filter(lambda x: x not in (let_identifiers+[None])[i:-1]))
        let_rec_expr.append([idf, expr])
    permuted_let_rec_expr = draw(st.permutations(let_rec_expr))
    return_value = draw(st.sampled_from(let_identifiers))
    return ['let-rec'] + permuted_let_rec_expr + [return_value] # type: ignore


@st.composite
def parsable_declare_rec_boolean_document(draw) -> RawSExpr:
    signal_names = draw(identifier_list)

    identifiers1 = draw(st.lists(elements=identifier().filter(lambda x: x not in signal_names), min_size=1, max_size=3, unique=True))
    declare_identifiers1 = draw(st.lists(st.sampled_from(identifiers1), min_size=1, unique=True))
    identifiers2 = draw(st.lists(elements=identifier().filter(lambda x: x not in signal_names and x not in declare_identifiers1), min_size=1, max_size=3, unique=True))
    declare_identifiers2 = draw(st.lists(st.sampled_from(identifiers2), min_size=1, unique=True))
    usable_identifiers1 = signal_names + identifiers1
    usable_identifiers2 = signal_names + declare_identifiers1 + identifiers2

    declare_rec_expr1 = []
    for (i, idf) in enumerate(identifiers1):
        expr: RawSExprList = draw(parsable_boolean(usable_identifiers1).filter(lambda x: x not in (identifiers1+[None])[i:-1]))
        if idf in declare_identifiers1:
            declare_rec_expr1.append(['declare', idf, expr])
        else:
            declare_rec_expr1.append([idf, expr])
    permuted_declare_rec_expr1 = draw(st.permutations(declare_rec_expr1))

    declare_rec_expr2 = []
    for (i, idf) in enumerate(identifiers2):
        expr: RawSExprList = draw(parsable_boolean(usable_identifiers2).filter(lambda x: x not in (identifiers2+[None])[i:-1]))
        if idf in declare_identifiers2:
            declare_rec_expr2.append(['declare', idf, expr])
        else:
            declare_rec_expr2.append([idf, expr])
    permuted_declare_rec_expr2 = draw(st.permutations(declare_rec_expr2))

    signal_list: RawSExprList = [['declare-input', signal] for signal in signal_names]

    return ['document'] + signal_list + [['declare-rec'] + permuted_declare_rec_expr1] + [['declare-rec'] + permuted_declare_rec_expr2]


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

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


    #document: str = random_ir(Bool, primitive_filter=lambda node_type: False if not issubclass(node_type, Bool) else True).example()
    #document: str = random_ir(Sequence, primitive_filter=lambda node_type: False if issubclass(node_type, Property) else True).example()
    document: str = random_ir(Property).example()

    logger.info(document)

    container1 = IrContainer()
    parse_document(parse_raw_sexpr(document), ir_container=container1)
    container1.bypass_placeholders()
    node_count_before: int = len(container1.nodes)
    logger.info('Number of nodes before pruning: %s', len(container1.nodes))
    container1.canonical_id_renaming()
    node_count_after: int = len(container1.nodes)
    output_document = container1.output_container()
    logger.info(output_document)
    logger.info('Number of nodes before pruning: %s', node_count_before)
    logger.info('Number of nodes after pruning: %s', node_count_after)

    return

    logger.info(random_ir(Sequence).example())
    logger.info(random_ir(Property).example())

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