
from logging import getLogger

from hypothesis import Verbosity, given, settings
from ir.base import IrContainer, NodeId, Property, RawSExpr
from ir.parsing import parse_document, parse_raw_sexpr

from tests.evaluate import (
    BoolMemoDict,
    FencepostPosition,
    MaybeBool,
    PropertyMemoDict,
    SequenceMemoDict,
    Trace,
    evaluate_bool,
    evaluate_property,
    sequence_matches,
)
from tests.strategies import random_ir_with_trace_simple

logger = getLogger(__name__)


def test_evaluate_bool():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare bool1 (and a b))
        (declare bool2 (or a b))
        (declare bool3 (true))
        (declare bool4 (and a (xor a b)))
        (declare bool5 (false))
        (declare bool6 a)
        (declare bool7 (not (and a b)))

    )"""

    doc_raw_sexpr: RawSExpr = parse_raw_sexpr(doc_str)
    container: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container)

    trace1: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    bool1: NodeId = container.get_node_id_by_name('bool1')
    bool2: NodeId = container.get_node_id_by_name('bool2')
    bool3: NodeId = container.get_node_id_by_name('bool3')
    bool4: NodeId = container.get_node_id_by_name('bool4')
    bool5: NodeId = container.get_node_id_by_name('bool5')
    bool6: NodeId = container.get_node_id_by_name('bool6')
    bool7: NodeId = container.get_node_id_by_name('bool7')

    bool_results: BoolMemoDict = {}

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 3)), bool_results) == True

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'
    assert evaluate_bool(bool1, container, trace1, FencepostPosition('unknown'), bool_results) == 'unknown'
    assert evaluate_bool(bool1, container, trace1, FencepostPosition('within_infinite_suffix'), bool_results) == 'top'

    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 3)), bool_results) == True

    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 3)), bool_results) == True

    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 3)), bool_results) == False

    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 3)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'
    assert evaluate_bool(bool5, container, trace1, FencepostPosition('unknown'), bool_results) == 'unknown'
    assert evaluate_bool(bool5, container, trace1, FencepostPosition('within_infinite_suffix'), bool_results) == 'top'

    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 3)), bool_results) == True
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 3)), bool_results) == True

    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 3)), bool_results) == False
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'



def test_evaluate_future_gclk():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare bool1 (future-gclk a))
        (declare bool2 (rising-gclk a (true)))
        (declare bool3 (falling-gclk a (true)))
        (declare bool4 (changing-gclk a (true)))

        (declare bool5 (not (future-gclk a)))
        (declare bool6 (and (not (falling-gclk a (true))) (falling-gclk b (true))))
        (declare bool7 (and (not (falling-gclk a (true))) (rising-gclk b (true))))
        (declare bool8 (and (not (changing-gclk a (true))) (changing-gclk a (true)) ))

    )"""

    doc_raw_sexpr: RawSExpr = parse_raw_sexpr(doc_str)
    container: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container)

    bool1: NodeId = container.get_node_id_by_name('bool1')
    bool2: NodeId = container.get_node_id_by_name('bool2')
    bool3: NodeId = container.get_node_id_by_name('bool3')
    bool4: NodeId = container.get_node_id_by_name('bool4')

    bool5: NodeId = container.get_node_id_by_name('bool5')
    bool6: NodeId = container.get_node_id_by_name('bool6')
    bool7: NodeId = container.get_node_id_by_name('bool7')
    bool8: NodeId = container.get_node_id_by_name('bool8')

    bool_results: BoolMemoDict = {}

    trace1: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='bot_omega')

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 2)), bool_results) == True

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 3)), bool_results) == 'top'
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'
    assert evaluate_bool(bool1, container, trace2, FencepostPosition(('at', 3)), bool_results) == 'bot'
    assert evaluate_bool(bool1, container, trace2, FencepostPosition(('at', 4)), bool_results) == 'bot'

    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 3)), bool_results) == False

    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 3)), bool_results) == 'top'

    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 3)), bool_results) == 'top'
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 3)), bool_results) == 'top'
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool5, container, trace2, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool5, container, trace2, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool5, container, trace2, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool5, container, trace2, FencepostPosition(('at', 3)), bool_results) == 'bot'
    assert evaluate_bool(bool5, container, trace2, FencepostPosition(('at', 4)), bool_results) == 'bot'

    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 3)), bool_results) == 'top'
    assert evaluate_bool(bool6, container, trace2, FencepostPosition(('at', 3)), bool_results) == 'bot'

    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 3)), bool_results) == False
    assert evaluate_bool(bool7, container, trace2, FencepostPosition(('at', 3)), bool_results) == False

    assert evaluate_bool(bool8, container, trace1, FencepostPosition(('at', 3)), bool_results) == 'top'
    assert evaluate_bool(bool8, container, trace2, FencepostPosition(('at', 3)), bool_results) == 'bot'


def test_evaluate_ite():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare bool1 (ite a (true) (false)))
        (declare bool2 (ite a b c))
        (declare bool3 (ite a (true) (true)))

    )"""

    doc_raw_sexpr: RawSExpr = parse_raw_sexpr(doc_str)
    container: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container)

    bool1: NodeId = container.get_node_id_by_name('bool1')
    bool2: NodeId = container.get_node_id_by_name('bool2')
    bool3: NodeId = container.get_node_id_by_name('bool3')

    bool_results: BoolMemoDict = {}

    trace1: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    trace2: Trace = Trace(finite_part=(), suffix='bot_omega')

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 3)), bool_results) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool3, container, trace2, FencepostPosition(('at', 0)), bool_results) == 'bot'


def test_evaluate_reg():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare bool1 (reg-gclk (true) a))
        (declare bool2 (reg-gclk (false) (or a b)) )
        (declare-rec (declare bool3 (reg-gclk (false) (or a bool3)) ))
        (declare-rec (bool_1 (reg-gclk (false) (or a bool_1)) )
                     (bool_2 (reg-gclk (false) (or b bool_2)) )
                     (declare bool4 (reg-gclk (false) (and bool_1 bool_2))))
        (declare bool5 (reg-gclk (false) (reg-gclk (false) a)))

    )"""

    doc_raw_sexpr: RawSExpr = parse_raw_sexpr(doc_str)
    container: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container)

    bool1: NodeId = container.get_node_id_by_name('bool1')
    bool2: NodeId = container.get_node_id_by_name('bool2')
    bool3: NodeId = container.get_node_id_by_name('bool3')
    bool4: NodeId = container.get_node_id_by_name('bool4')
    bool5: NodeId = container.get_node_id_by_name('bool5')

    bool_results: BoolMemoDict = {}

    trace1: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 0)), bool_results) == True
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 3)), bool_results) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 3)), bool_results) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 1)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 3)), bool_results) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 2)), bool_results) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 3)), bool_results) == True
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'

    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 0)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 1)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 2)), bool_results) == True
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 3)), bool_results) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 4)), bool_results) == 'top'
    assert evaluate_bool(bool5, container, trace1, FencepostPosition('within_infinite_suffix'), bool_results) == 'top'


def test_evaluate_sequence_matches():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare bool1 (and a b))
        (declare bool2 (or a b))
        (declare bool_true (seq-bool (true)))

        (declare seq0 (seq-bool a))

        (declare seq1 (seq-or (seq-bool a) (seq-bool b)))

        (declare seq2 (seq-concat
            (seq-bool bool1)
            (seq-bool bool2)
        ))

        (declare seq3
            (seq-repeat (range 1 $) bool_true)
        )

        (declare seq4
            (seq-repeat (range 2 3) bool_true)
        )

        (declare seq5 (seq-concat
            (seq-bool a)
            (seq-bool b)
            (seq-repeat (range 1 $) bool_true)
        ))

        (declare seq6 (seq-fusion
            (seq-repeat (range 1 3) bool_true)
            (seq-bool a)
            (seq-bool b)
        ))

        (declare seq7 (seq-fusion
            (seq-repeat (range 4 4) bool_true)
            (seq-bool a)
            (seq-bool b)
        ))

        (declare seq8 (seq-fusion
            (seq-repeat (range 4 4) bool_true)
            (seq-bool (not a))
        ))

        (declare seq9 (seq-intersect
            (seq-repeat (range 2 $) bool_true)
            (seq-concat (seq-bool a) (seq-bool b))
        ))

        (declare seq10 (seq-intersect
            (seq-repeat (range 4 5) bool_true)
            (seq-repeat (range 4 7) bool_true)
        ))

        (declare seq11 (seq-first-match
            (seq-repeat (range 1 5) bool_true)
        ))

        (declare seq12 (seq-first-match
            (seq-repeat (range 5 $) bool_true)
        ))

        (declare seq13 (seq-first-match (seq-intersect
            (seq-repeat (range 4 5) bool_true)
            (seq-repeat (range 4 7) bool_true)
        )))

        (declare seq14 (seq-concat (seq-bool bool1)))
        (declare seq15 (seq-intersect (seq-bool bool1)))
        (declare seq16 (seq-or (seq-bool bool1)))
        (declare seq17 (seq-fusion (seq-bool bool1)))

        (declare seq18 (seq-intersect
            (seq-repeat (range 1 $) (seq-concat bool_true bool_true))
            (seq-repeat (range 1 $) (seq-concat bool_true bool_true bool_true))
        ))


    )"""

    doc_raw_sexpr: RawSExpr = parse_raw_sexpr(doc_str)
    container: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container)

    seq0: NodeId = container.get_node_id_by_name('seq0')
    seq1: NodeId = container.get_node_id_by_name('seq1')
    seq2: NodeId = container.get_node_id_by_name('seq2')
    seq3: NodeId = container.get_node_id_by_name('seq3')
    seq4: NodeId = container.get_node_id_by_name('seq4')
    seq5: NodeId = container.get_node_id_by_name('seq5')
    seq6: NodeId = container.get_node_id_by_name('seq6')
    seq7: NodeId = container.get_node_id_by_name('seq7')
    seq8: NodeId = container.get_node_id_by_name('seq8')
    seq9: NodeId = container.get_node_id_by_name('seq9')
    seq10: NodeId = container.get_node_id_by_name('seq10')
    seq11: NodeId = container.get_node_id_by_name('seq11')
    seq12: NodeId = container.get_node_id_by_name('seq12')
    seq13: NodeId = container.get_node_id_by_name('seq13')
    seq14: NodeId = container.get_node_id_by_name('seq14')
    seq15: NodeId = container.get_node_id_by_name('seq15')
    seq16: NodeId = container.get_node_id_by_name('seq16')
    seq17: NodeId = container.get_node_id_by_name('seq17')
    seq18: NodeId = container.get_node_id_by_name('seq18')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 2)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 4))])
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 4)), bool_results, seq_results) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq0, container, trace1, FencepostPosition('within_infinite_suffix'), bool_results, seq_results) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq0, container, trace1, FencepostPosition('unknown'), bool_results, seq_results) == frozenset([FencepostPosition('unknown')])

    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 2)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 4))])

    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 2)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 4)), bool_results, seq_results) == frozenset([FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq3, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset([FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq3, container, trace1, FencepostPosition(('at', 3)), bool_results, seq_results) == \
        frozenset([FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq4, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset([FencepostPosition(('at', 2)), FencepostPosition(('at', 3))])
    assert sequence_matches(seq4, container, trace1, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset([FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq5, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset([FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq6, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq7, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 4))])
    assert sequence_matches(seq8, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset()

    assert sequence_matches(seq9, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq10, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 4)), FencepostPosition('unknown')])

    assert sequence_matches(seq11, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq12, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq13, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition('unknown')])

    assert sequence_matches(seq14, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq14, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq15, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq15, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq16, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq16, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq17, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq17, container, trace1, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset()

    assert sequence_matches(seq18, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition('unknown')])

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='bot_omega')

    assert sequence_matches(seq0, container, trace2, FencepostPosition(('at', 4)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq0, container, trace2, FencepostPosition('within_infinite_suffix'), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq2, container, trace2, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq2, container, trace2, FencepostPosition(('at', 4)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq3, container, trace2, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 4))])
    assert sequence_matches(seq12, container, trace2, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset()

    trace3: Trace = Trace(finite_part=(
        'top',
        frozenset(['b']),
        frozenset([]),
        'bot',
    ), suffix='top_omega')

    assert sequence_matches(seq0, container, trace3, FencepostPosition(('at', 0)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq1, container, trace3, FencepostPosition(('at', 1)), bool_results, seq_results) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq1, container, trace3, FencepostPosition(('at', 3)), bool_results, seq_results) == frozenset()
    assert sequence_matches(seq3, container, trace3, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset([FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))])

    assert sequence_matches(seq11, container, trace3, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset([FencepostPosition(('at', 1)), FencepostPosition(('at', 2))])




def test_evaluate_prop_strong_weak():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare prop1 (prop-strong-bool (and a b)))
        (declare prop2 (prop-strong (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare prop3 (prop-strong (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ) ))

        (declare prop1_w (prop-weak-bool (and a b)))
        (declare prop2_w (prop-weak (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare prop3_w (prop-weak (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ) ))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))

        (declare prop4 (prop-strong (seq-or seq1 seq2)))
        (declare prop5 (prop-strong (seq-intersect seq1 seq2)))

        (declare prop4_w (prop-weak (seq-or seq1 seq2)))
        (declare prop5_w (prop-weak (seq-intersect seq1 seq2)))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop3: NodeId = container.get_node_id_by_name('prop3')

    prop1_w: NodeId = container.get_node_id_by_name('prop1_w')
    prop2_w: NodeId = container.get_node_id_by_name('prop2_w')
    prop3_w: NodeId = container.get_node_id_by_name('prop3_w')

    prop4: NodeId = container.get_node_id_by_name('prop4')
    prop5: NodeId = container.get_node_id_by_name('prop5')
    prop4_w: NodeId = container.get_node_id_by_name('prop4_w')
    prop5_w: NodeId = container.get_node_id_by_name('prop5_w')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset(['a']),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a']),
    ), suffix='bot_omega')

    trace4: Trace = Trace(finite_part=(
        frozenset(['a']),
    ), suffix='end')

    trace5: Trace = Trace(finite_part=(), suffix='top_omega')
    trace6: Trace = Trace(finite_part=(), suffix='bot_omega')
    trace7: Trace = Trace(finite_part=(), suffix='end')

    trace8: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset([]),
        frozenset(['a']),
        frozenset(['a', 'b']),
    ), suffix='top_omega')


    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    # strong

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace5, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace6, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace7, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace4, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop3, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace5, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace6, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace7, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop4, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop5, container, trace8, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace2, bool_results, seq_results, prop_results) == 'unknown'

    # weak

    assert evaluate_property(prop1_w, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1_w, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1_w, container, trace5, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1_w, container, trace6, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1_w, container, trace7, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop2_w, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2_w, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2_w, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2_w, container, trace4, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop3_w, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3_w, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3_w, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3_w, container, trace4, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3_w, container, trace5, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3_w, container, trace6, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3_w, container, trace7, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop4_w, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5_w, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop5_w, container, trace8, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4_w, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5_w, container, trace2, bool_results, seq_results, prop_results) == 'unknown'


def test_evaluate_prop_and_or():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare prop_f (prop-strong (seq-bool (false)) ) )
        (declare prop_t (prop-strong (seq-bool (true)) ) )

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare prop_unknown (prop-weak (seq-intersect seq1 seq2)))

        (declare prop_and_1 (prop-and prop_f prop_t))
        (declare prop_or_1 (prop-or prop_f prop_t))

        (declare prop_and_2 (prop-and prop_t prop_unknown prop_t ))
        (declare prop_or_2 (prop-or prop_f prop_unknown prop_t))
        (declare prop_and_3 (prop-and prop_t prop_unknown prop_f ))
        (declare prop_or_3 (prop-or prop_f prop_unknown prop_f))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop_and_1: NodeId = container.get_node_id_by_name('prop_and_1')
    prop_or_1: NodeId = container.get_node_id_by_name('prop_or_1')
    prop_and_2: NodeId = container.get_node_id_by_name('prop_and_2')
    prop_or_2: NodeId = container.get_node_id_by_name('prop_or_2')
    prop_and_3: NodeId = container.get_node_id_by_name('prop_and_3')
    prop_or_3: NodeId = container.get_node_id_by_name('prop_or_3')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset(['a']),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop_and_1, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_or_1,  container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_and_2, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_or_2,  container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_and_3, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_or_3,  container, trace1, bool_results, seq_results, prop_results) == 'unknown'


def test_evaluate_prop_nexttime_strong_nexttime():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare prop1 (prop-strong-bool (and a b)))
        (declare prop2 (prop-strong (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare prop2_w (prop-weak (seq-concat (seq-bool a) (seq-bool b)) ))

        (declare prop_n1 (prop-nexttime 1 prop1))
        (declare prop_n2 (prop-nexttime 3 prop1))
        (declare prop_n3 (prop-nexttime 6 prop1))
        (declare prop_n4 (prop-nexttime 3 prop2))
        (declare prop_n5 (prop-nexttime 3 prop2_w))

        (declare prop_sn1 (prop-strong-nexttime 1 prop1))
        (declare prop_sn2 (prop-strong-nexttime 3 prop1))
        (declare prop_sn3 (prop-strong-nexttime 6 prop1))
        (declare prop_sn4 (prop-strong-nexttime 3 prop2))
        (declare prop_sn5 (prop-strong-nexttime 3 prop2_w))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop_n1: NodeId = container.get_node_id_by_name('prop_n1')
    prop_n2: NodeId = container.get_node_id_by_name('prop_n2')
    prop_n3: NodeId = container.get_node_id_by_name('prop_n3')
    prop_n4: NodeId = container.get_node_id_by_name('prop_n4')
    prop_n5: NodeId = container.get_node_id_by_name('prop_n5')

    prop_sn1: NodeId = container.get_node_id_by_name('prop_sn1')
    prop_sn2: NodeId = container.get_node_id_by_name('prop_sn2')
    prop_sn3: NodeId = container.get_node_id_by_name('prop_sn3')
    prop_sn4: NodeId = container.get_node_id_by_name('prop_sn4')
    prop_sn5: NodeId = container.get_node_id_by_name('prop_sn5')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset(['a']),
        frozenset(['a', 'b']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a']),
    ), suffix='bot_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop_n1, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_n2, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_n3, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_n4, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_n5, container, trace1, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop_sn1, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_sn2, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_sn3, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_sn4, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_sn5, container, trace1, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop_n1,  container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_n1,  container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_sn1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_sn1, container, trace3, bool_results, seq_results, prop_results) == False


def test_evaluate_prop_accept_reject_on():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare prop1 (prop-strong (seq-concat (seq-bool a) (seq-bool b) (seq-bool a) (seq-bool b) (seq-bool a) ) ))
        (declare prop2 (prop-strong (seq-concat (seq-bool a) (seq-bool b) (seq-bool a) (seq-bool b) ) ))

        (declare prop_acc_1 (prop-accept-on c prop1) )
        (declare prop_rej_1 (prop-reject-on c prop2) )

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare prop_unknown (prop-weak (seq-intersect seq1 seq2)))

        (declare prop_acc_unknown (prop-accept-on c prop_unknown) )
        (declare prop_rej_unknown (prop-reject-on c prop_unknown) )

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop_acc_1: NodeId = container.get_node_id_by_name('prop_acc_1')
    prop_rej_1: NodeId = container.get_node_id_by_name('prop_rej_1')
    prop_acc_unknown: NodeId = container.get_node_id_by_name('prop_acc_unknown')
    prop_rej_unknown: NodeId = container.get_node_id_by_name('prop_rej_unknown')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='bot_omega')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset(['a']),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop_acc_1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_rej_1, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_acc_unknown, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_rej_unknown, container, trace1, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop_acc_1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_rej_1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_acc_unknown, container, trace2, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_rej_unknown, container, trace2, bool_results, seq_results, prop_results) == 'unknown'


def test_evaluate_prop_overlapped_implication():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare seq_rep (seq-repeat (range 1 $) (seq-bool (true)) ))

        (declare prop0 (prop-overlapped-implication (seq-concat seq_rep (seq-bool c)) (prop-weak-bool c) ))
        (declare prop1 (prop-overlapped-implication (seq-concat seq_rep (seq-bool c)) (prop-nexttime 1 (prop-weak-bool a)) ))
        (declare prop2 (prop-overlapped-implication (seq-concat seq_rep (seq-bool c)) (prop-nexttime 1 (prop-weak-bool b)) ))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare seq_unknown (seq-intersect seq1 seq2))

        (declare prop_unknown (prop-overlapped-implication seq_unknown (prop-nexttime 1 (prop-weak-bool a))))


        (declare prop3 (prop-overlapped-implication seq_rep (prop-weak-bool (true)) ))
        (declare prop4 (prop-overlapped-implication seq_rep (prop-weak-bool a) ))

        (declare prop5 (prop-overlapped-implication
            (seq-concat (seq-bool a) (seq-bool b))
            (prop-weak (seq-concat (seq-bool b) (seq-bool a) (seq-bool a) (seq-bool c)))
        ))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop0: NodeId = container.get_node_id_by_name('prop0')
    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop_unknown: NodeId = container.get_node_id_by_name('prop_unknown')
    prop3: NodeId = container.get_node_id_by_name('prop3')
    prop4: NodeId = container.get_node_id_by_name('prop4')
    prop5: NodeId = container.get_node_id_by_name('prop5')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='bot_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop0, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop_unknown, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_unknown, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_unknown, container, trace3, bool_results, seq_results, prop_results) == 'unknown'

    assert evaluate_property(prop0, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop0, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop3, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop4, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop5, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace3, bool_results, seq_results, prop_results) == False


def test_evaluate_prop_overlapped_followed_by():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare seq_rep (seq-repeat (range 1 $) (seq-bool (true)) ))

        (declare prop0 (prop-overlapped-followed-by (seq-concat seq_rep (seq-bool c)) (prop-weak-bool c) ))
        (declare prop1 (prop-overlapped-followed-by (seq-concat seq_rep (seq-bool c)) (prop-nexttime 1 (prop-weak-bool a)) ))
        (declare prop2 (prop-overlapped-followed-by (seq-concat seq_rep (seq-bool c)) (prop-nexttime 1 (prop-weak-bool b)) ))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare seq_unknown (seq-intersect seq1 seq2))

        (declare prop_unknown (prop-overlapped-followed-by seq_unknown (prop-nexttime 1 (prop-weak-bool a))))


        (declare prop3 (prop-overlapped-followed-by seq_rep (prop-weak-bool (true)) ))
        (declare prop4 (prop-overlapped-followed-by seq_rep (prop-weak-bool a) ))

        (declare prop5 (prop-overlapped-followed-by
            (seq-concat (seq-bool a) (seq-bool b))
            (prop-weak (seq-concat (seq-bool b) (seq-bool a) (seq-bool a) (seq-bool c)))
        ))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop0: NodeId = container.get_node_id_by_name('prop0')
    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop_unknown: NodeId = container.get_node_id_by_name('prop_unknown')
    prop3: NodeId = container.get_node_id_by_name('prop3')
    prop4: NodeId = container.get_node_id_by_name('prop4')
    prop5: NodeId = container.get_node_id_by_name('prop5')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='bot_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop0, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop0, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop0, container, trace3, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop_unknown, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_unknown, container, trace2, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_unknown, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop3, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace3, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop4, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop4, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop4, container, trace3, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop5, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace3, bool_results, seq_results, prop_results) == False


def test_evaluate_weak_unknown():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare seq_rep (seq-repeat (range 1 $) (seq-bool (true)) ))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare prop_unknown (prop-weak (seq-intersect seq1 seq2)))

        (declare prop1 (prop-weak seq_rep))

    )
    """

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop_unknown: NodeId = container.get_node_id_by_name('prop_unknown')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace4: Trace = Trace(finite_part=(
    ), suffix='end')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace4, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_unknown, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_unknown, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop_unknown, container, trace3, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_unknown, container, trace4, bool_results, seq_results, prop_results) == 'unknown'


def test_evaluate_prop_until():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare seq_rep (seq-repeat (range 1 $) (seq-bool (true)) ))

        (declare prop1 (prop-until (prop-weak-bool a) (prop-weak-bool c)))
        (declare prop2 (prop-until (prop-weak-bool a) (prop-weak-bool (not b))))
        (declare prop3 (prop-until (prop-weak seq_rep) (prop-weak-bool (and c a (not b)) ) ))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare prop_unknown (prop-weak (seq-intersect seq1 seq2)))

        (declare prop4 (prop-until prop_unknown (prop-weak-bool (and c a (not b))) ))
        (declare prop5 (prop-until (prop-weak seq_rep) prop_unknown))
        (declare prop6 (prop-until prop_unknown (prop-weak seq_rep)))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop3: NodeId = container.get_node_id_by_name('prop3')
    prop4: NodeId = container.get_node_id_by_name('prop4')
    prop5: NodeId = container.get_node_id_by_name('prop5')
    prop6: NodeId = container.get_node_id_by_name('prop6')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='bot_omega')

    trace4: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop3, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop4, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace4, bool_results, seq_results, prop_results) == 'unknown'

    assert evaluate_property(prop5, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop5, container, trace4, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop6, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop6, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop6, container, trace3, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop6, container, trace4, bool_results, seq_results, prop_results) == True


def test_evaluate_prop_strong_until_with():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare seq_rep (seq-repeat (range 1 $) (seq-bool (true)) ))

        (declare prop1 (prop-strong-until-with (prop-weak-bool b) (prop-weak-bool c)))
        (declare prop2 (prop-strong-until-with (prop-weak-bool a) (prop-weak-bool (not b))))
        (declare prop3 (prop-strong-until-with (prop-weak seq_rep) (prop-weak-bool (and c a (not b)) ) ))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare prop_unknown (prop-weak (seq-intersect seq1 seq2)))

        (declare prop4 (prop-strong-until-with prop_unknown (prop-weak-bool (and c a (not b))) ))
        (declare prop5 (prop-strong-until-with (prop-weak seq_rep) prop_unknown))
        (declare prop6 (prop-strong-until-with prop_unknown (prop-weak seq_rep)))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop3: NodeId = container.get_node_id_by_name('prop3')
    prop4: NodeId = container.get_node_id_by_name('prop4')
    prop5: NodeId = container.get_node_id_by_name('prop5')
    prop6: NodeId = container.get_node_id_by_name('prop6')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='bot_omega')

    trace4: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace4, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace4, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop3, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace4, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop4, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace4, bool_results, seq_results, prop_results) == 'unknown'

    assert evaluate_property(prop5, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop5, container, trace2, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop5, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop5, container, trace4, bool_results, seq_results, prop_results) == 'unknown'

    assert evaluate_property(prop6, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop6, container, trace2, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop6, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop6, container, trace4, bool_results, seq_results, prop_results) == 'unknown'


def test_evaluate_prop_not():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare seq_rep (seq-repeat (range 2 $) (seq-bool (true)) ))

        (declare prop1 (prop-not (prop-weak seq_rep)))
        (declare prop2 (prop-not (prop-strong seq_rep)))

        (declare seq1 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b)) ))
        (declare seq2 (seq-repeat (range 1 $) (seq-concat (seq-bool a) (seq-bool b) (seq-bool a)) ))
        (declare prop_unknown (prop-not (prop-weak (seq-intersect seq1 seq2))))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop_unknown: NodeId = container.get_node_id_by_name('prop_unknown')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='bot_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop_unknown, container, trace1, bool_results, seq_results, prop_results) == 'unknown'
    assert evaluate_property(prop_unknown, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_unknown, container, trace3, bool_results, seq_results, prop_results) == 'unknown'


def test_evaluate_prop_refuted():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare seq_rep (seq-repeat (range 1 $) (seq-bool (true)) ))
        (declare a_rep (seq-repeat (range 1 $) (seq-bool a) ))

        (declare a_something (seq-concat (seq-bool a) seq_rep))
        (declare b_something (seq-concat (seq-bool b) seq_rep))
        (declare something_a (seq-concat seq_rep (seq-bool a)))
        (declare something_a_star (seq-concat seq_rep a_rep))
        (declare a_something_or_b_something (seq-or a_something b_something))

        (declare prop0 (prop-refuted seq_rep))
        (declare prop1 (prop-refuted a_rep))
        (declare prop2 (prop-refuted a_something))
        (declare prop3 (prop-refuted something_a))
        (declare prop4 (prop-refuted something_a_star))
        (declare prop5 (prop-refuted a_something_or_b_something))

        (declare prop_w1 (prop-weak a_something))
        (declare prop_w2 (prop-weak a_rep))

        (declare prop1_check (prop-not (prop-weak a_rep)))
        (declare prop2_check (prop-not (prop-weak a_something)))

    )
    """

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    seq_rep: NodeId = container.get_node_id_by_name('seq_rep')
    a_rep: NodeId = container.get_node_id_by_name('a_rep')
    a_something: NodeId = container.get_node_id_by_name('a_something')
    prop_w1: NodeId = container.get_node_id_by_name('prop_w1')
    prop_w2: NodeId = container.get_node_id_by_name('prop_w2')
    prop0: NodeId = container.get_node_id_by_name('prop0')
    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')
    prop3: NodeId = container.get_node_id_by_name('prop3')
    prop4: NodeId = container.get_node_id_by_name('prop4')
    prop5: NodeId = container.get_node_id_by_name('prop5')
    prop1_check: NodeId = container.get_node_id_by_name('prop1_check')
    prop2_check: NodeId = container.get_node_id_by_name('prop2_check')

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace2: Trace = Trace(finite_part=(
        frozenset(['b']),
        frozenset(['b', 'c']),
        frozenset(['a']),
        frozenset(['a', 'b', 'c']),
    ), suffix='end')

    trace3: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    trace4: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
    ), suffix='bot_omega')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert sequence_matches(seq_rep, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset({FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))})
    assert sequence_matches(a_rep, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset({FencepostPosition(('at', 1))})
    assert sequence_matches(a_something, container, trace1, FencepostPosition(('at', 0)), bool_results, seq_results) == \
        frozenset({FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))})

    assert evaluate_property(prop_w1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop_w2, container, trace1, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop0, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop5, container, trace1, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop0, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop5, container, trace2, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop0, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == False
    # note on semantics: because of the top_omega suffix
    # refuted (= not weak) is evaluated optimistically, and the result is true
    # because in the future the sequence can still be refuted
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop3, container, trace3, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop4, container, trace3, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop5, container, trace3, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1_check, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2_check, container, trace3, bool_results, seq_results, prop_results) == True

    assert evaluate_property(prop0, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace4, bool_results, seq_results, prop_results) == False
    # note on semantics: because of the bot_omega suffix
    # refuted (= not weak) is evaluated pessimistically, and the result is false
    # because in the future the sequence being refuted might fail
    assert evaluate_property(prop2, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop3, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop4, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop5, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1_check, container, trace4, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2_check, container, trace4, bool_results, seq_results, prop_results) == False


def test_evaluate_prop_not_weak_future_gclk():
    doc_str: str = """(document
        (declare-input 0)

        (declare prop1 (let-rec
            (step0 (future-gclk (true)))
            (step1 (prop-weak-bool step0))
            (step2 (prop-not step1)) step2))

        (declare prop2 (prop-strong-bool (future-gclk (true))))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')

    trace1 = Trace(finite_part=(frozenset(),), suffix='top_omega')
    trace2 = Trace(finite_part=(frozenset(),), suffix='bot_omega')
    trace3 = Trace(finite_part=(frozenset(),), suffix='end')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False


def test_evaluate_prop_not_not_until():

    doc_str: str = """(document
        (declare-input 0)
        (declare-input 00)

        (declare prop1 (let-rec
            (step0 (prop-until (prop-weak-bool 0) (prop-weak-bool 00)))
            (step1 (prop-not step0))
            (step2 (prop-not step1)) step2))

        (declare prop2 (prop-until (prop-weak-bool 0) (prop-weak-bool 00)))

    )"""

    trace1 = Trace(finite_part=(frozenset({'00'}), frozenset()), suffix='end')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == True


def test_evaluate_prop_recursive():

    doc_str: str = """(document
        (declare-input a)

        (declare-rec (declare prop1
            (prop-and
                (prop-weak-bool a)
                (prop-overlapped-implication
                    (seq-repeat (range 2 2) (seq-bool (constant true)))
                    prop1))))
    )"""

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
    ), suffix='end')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset(),
        frozenset({'a'}),
    ), suffix='end')

    trace3 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
    ), suffix='bot_omega')

    trace4 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
    ), suffix='top_omega')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace4, bool_results, seq_results, prop_results) == True


def test_evaluate_prop_mutually_recursive():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare-rec
            (declare prop1 (prop-and
                (prop-weak-bool a)
                (prop-overlapped-implication
                    (seq-repeat (range 2 2) (seq-bool (constant true)))
                     prop2)))
            (declare prop2 (prop-and
                (prop-weak-bool b)
                (prop-overlapped-implication
                    (seq-repeat (range 2 2) (seq-bool (constant true)))
                    prop1))))
    )"""

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'a'}),
        frozenset({'b'}),
    ), suffix='end')

    trace2 = Trace(finite_part=(
        frozenset({'b'}),
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'a'}),
    ), suffix='end')

    trace3 = Trace(finite_part=(
        frozenset({'a', 'b'}),
        frozenset({'a', 'b'}),
        frozenset(),
        frozenset({'a', 'b'}),
    ), suffix='top_omega')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    prop1: NodeId = container.get_node_id_by_name('prop1')
    prop2: NodeId = container.get_node_id_by_name('prop2')

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    assert evaluate_property(prop1, container, trace1, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop1, container, trace2, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop1, container, trace3, bool_results, seq_results, prop_results) == False

    assert evaluate_property(prop2, container, trace1, bool_results, seq_results, prop_results) == False
    assert evaluate_property(prop2, container, trace2, bool_results, seq_results, prop_results) == True
    assert evaluate_property(prop2, container, trace3, bool_results, seq_results, prop_results) == False


@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given(random_ir_with_trace_simple(final_node_type=Property))
def test_evaluate_random_no_error(doc_and_trace):

    doc: str = doc_and_trace[0]
    trace: Trace = doc_and_trace[1]

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), container)

    root_node_id: NodeId = container.get_sink_nodes()[0]

    bool_results: BoolMemoDict = {}
    seq_results: SequenceMemoDict = {}
    prop_results: PropertyMemoDict = {}

    result: MaybeBool = evaluate_property(root_node_id, container, trace, bool_results, seq_results, prop_results)

    logger.debug('doc: %s', doc)
    logger.debug('trace: %s', trace)
    logger.debug('result: %s', result)
