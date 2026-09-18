
from ir.base import IrContainer, NodeId, RawSExpr
from ir.parsing import parse_document, parse_raw_sexpr

from tests.evaluate import FencepostPosition, Trace, evaluate_bool, sequence_matches


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
        (declare bool7 (future-gclk a))
        (declare bool8 (rising-gclk a (true)))
        (declare bool9 (falling-gclk a (true)))
        (declare bool10 (changing-gclk a (true)))
        (declare bool11 (not (and a b)))
        (declare bool12 (not (future-gclk a)))
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
    bool8: NodeId = container.get_node_id_by_name('bool8')
    bool9: NodeId = container.get_node_id_by_name('bool9')
    bool10: NodeId = container.get_node_id_by_name('bool10')
    bool11: NodeId = container.get_node_id_by_name('bool11')
    bool12: NodeId = container.get_node_id_by_name('bool12')

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 0))) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 3))) == True

    assert evaluate_bool(bool1, container, trace1, FencepostPosition(('at', 4))) == True
    assert evaluate_bool(bool1, container, trace1, FencepostPosition('unknown')) == 'unknown'
    assert evaluate_bool(bool1, container, trace1, FencepostPosition('within_infinite_suffix')) == True

    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 1))) == True
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool2, container, trace1, FencepostPosition(('at', 3))) == True

    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 1))) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 2))) == True
    assert evaluate_bool(bool3, container, trace1, FencepostPosition(('at', 3))) == True

    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool4, container, trace1, FencepostPosition(('at', 3))) == False

    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 0))) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 3))) == False
    assert evaluate_bool(bool5, container, trace1, FencepostPosition(('at', 4))) == True
    assert evaluate_bool(bool5, container, trace1, FencepostPosition('unknown')) == 'unknown'
    assert evaluate_bool(bool5, container, trace1, FencepostPosition('within_infinite_suffix')) == True

    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool6, container, trace1, FencepostPosition(('at', 3))) == True

    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 0))) == False
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 2))) == True
    assert evaluate_bool(bool7, container, trace1, FencepostPosition(('at', 3))) == 'unknown'

    assert evaluate_bool(bool8, container, trace1, FencepostPosition(('at', 0))) == False
    assert evaluate_bool(bool8, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool8, container, trace1, FencepostPosition(('at', 2))) == True
    assert evaluate_bool(bool8, container, trace1, FencepostPosition(('at', 3))) == 'unknown'

    assert evaluate_bool(bool9, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool9, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool9, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool9, container, trace1, FencepostPosition(('at', 3))) == 'unknown'

    assert evaluate_bool(bool10, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool10, container, trace1, FencepostPosition(('at', 1))) == False
    assert evaluate_bool(bool10, container, trace1, FencepostPosition(('at', 2))) == True
    assert evaluate_bool(bool10, container, trace1, FencepostPosition(('at', 3))) == 'unknown'
    assert evaluate_bool(bool10, container, trace1, FencepostPosition(('at', 4))) == True

    assert evaluate_bool(bool11, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool11, container, trace1, FencepostPosition(('at', 1))) == True
    assert evaluate_bool(bool11, container, trace1, FencepostPosition(('at', 2))) == True
    assert evaluate_bool(bool11, container, trace1, FencepostPosition(('at', 3))) == False
    assert evaluate_bool(bool11, container, trace1, FencepostPosition(('at', 4))) == True

    assert evaluate_bool(bool12, container, trace1, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool12, container, trace1, FencepostPosition(('at', 1))) == True
    assert evaluate_bool(bool12, container, trace1, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool12, container, trace1, FencepostPosition(('at', 3))) == 'unknown'
    assert evaluate_bool(bool12, container, trace1, FencepostPosition(('at', 4))) == True

    trace2: Trace = Trace(finite_part=(
        frozenset(['a']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='bot_omega')

    assert evaluate_bool(bool12, container, trace2, FencepostPosition(('at', 0))) == True
    assert evaluate_bool(bool12, container, trace2, FencepostPosition(('at', 1))) == True
    assert evaluate_bool(bool12, container, trace2, FencepostPosition(('at', 2))) == False
    assert evaluate_bool(bool12, container, trace2, FencepostPosition(('at', 3))) == 'unknown'
    assert evaluate_bool(bool12, container, trace2, FencepostPosition(('at', 4))) == False


def test_sequence_matches_1():

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

    trace1: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='top_omega')

    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 1))) == frozenset()
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 2))) == frozenset()
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 3))) == frozenset([FencepostPosition(('at', 4))])
    assert sequence_matches(seq0, container, trace1, FencepostPosition(('at', 4))) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq0, container, trace1, FencepostPosition('within_infinite_suffix')) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq0, container, trace1, FencepostPosition('unknown')) == frozenset([FencepostPosition('unknown')])

    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 1))) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 2))) == frozenset()
    assert sequence_matches(seq1, container, trace1, FencepostPosition(('at', 3))) == frozenset([FencepostPosition(('at', 4))])

    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 1))) == frozenset()
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 2))) == frozenset()
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 3))) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq2, container, trace1, FencepostPosition(('at', 4))) == frozenset([FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq3, container, trace1, FencepostPosition(('at', 0))) == \
        frozenset([FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq3, container, trace1, FencepostPosition(('at', 3))) == \
        frozenset([FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq4, container, trace1, FencepostPosition(('at', 0))) == \
        frozenset([FencepostPosition(('at', 2)), FencepostPosition(('at', 3))])
    assert sequence_matches(seq4, container, trace1, FencepostPosition(('at', 3))) == frozenset([FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq5, container, trace1, FencepostPosition(('at', 0))) == \
        frozenset([FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')])

    assert sequence_matches(seq6, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq7, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 4))])
    assert sequence_matches(seq8, container, trace1, FencepostPosition(('at', 0))) == frozenset()

    assert sequence_matches(seq9, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq10, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 4)), FencepostPosition('unknown')])

    assert sequence_matches(seq11, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq12, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition('within_infinite_suffix')])
    assert sequence_matches(seq13, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition('unknown')])

    assert sequence_matches(seq14, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq14, container, trace1, FencepostPosition(('at', 1))) == frozenset()
    assert sequence_matches(seq15, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq15, container, trace1, FencepostPosition(('at', 1))) == frozenset()
    assert sequence_matches(seq16, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq16, container, trace1, FencepostPosition(('at', 1))) == frozenset()
    assert sequence_matches(seq17, container, trace1, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq17, container, trace1, FencepostPosition(('at', 1))) == frozenset()

    trace2: Trace = Trace(finite_part=(
        frozenset(['a', 'b']),
        frozenset(['b']),
        frozenset([]),
        frozenset(['a', 'b']),
    ), suffix='bot_omega')

    assert sequence_matches(seq0, container, trace2, FencepostPosition(('at', 4))) == frozenset()
    assert sequence_matches(seq0, container, trace2, FencepostPosition('within_infinite_suffix')) == frozenset()
    assert sequence_matches(seq2, container, trace2, FencepostPosition(('at', 3))) == frozenset()
    assert sequence_matches(seq2, container, trace2, FencepostPosition(('at', 4))) == frozenset()
    assert sequence_matches(seq3, container, trace2, FencepostPosition(('at', 3))) == frozenset([FencepostPosition(('at', 4))])
    assert sequence_matches(seq12, container, trace2, FencepostPosition(('at', 0))) == frozenset()

    trace3: Trace = Trace(finite_part=(
        'top',
        frozenset(['b']),
        frozenset([]),
        'bot',
    ), suffix='top_omega')

    assert sequence_matches(seq0, container, trace3, FencepostPosition(('at', 0))) == frozenset([FencepostPosition(('at', 1))])
    assert sequence_matches(seq1, container, trace3, FencepostPosition(('at', 1))) == frozenset([FencepostPosition(('at', 2))])
    assert sequence_matches(seq1, container, trace3, FencepostPosition(('at', 3))) == frozenset()
    assert sequence_matches(seq3, container, trace3, FencepostPosition(('at', 0))) == \
        frozenset([FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))])

    assert sequence_matches(seq11, container, trace3, FencepostPosition(('at', 0))) == \
        frozenset([FencepostPosition(('at', 1)), FencepostPosition(('at', 2))])
