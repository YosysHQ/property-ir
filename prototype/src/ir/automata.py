
from typing import Literal

from .base import IrContainer, PropertyIrNode, RawSExprList
from .primitives.automata_primitives import *
from .primitives.simple_primitives import *
from .rewriting import (
    apply_rules,
    construct_rewritten_container,
    RewriteRule,
    RewriteRuleGenerator,
)



def get_split_seq_repeat_rewrite_rule(container: IrContainer, node_id: NodeId) -> RewriteRule:
    """Get the rewrite rule to break seq-repeat primitives up into a concatenation
    of two seq-repeat primitives."""

    node: PropertyIrNode = container[node_id]

    if not isinstance(node, SeqRepeat):
        raise TypeError(f'Cannot generate seq-repeat rewrite rule for node {node} with wrong node type')

    repeat_range: Range = node.child1

    lower_bound: int = repeat_range.lower_bound
    upper_bound: int | Literal['$'] = repeat_range.upper_bound.value

    if lower_bound == 1:
        return ([], []) # nothing to do

    if type(upper_bound) is int:
        rhs: RawSExprList = ['seq-concat',
            ['seq-repeat', ['range', str(lower_bound - 1), str(lower_bound - 1)], '<seq>'],
            ['seq-repeat', ['range', '1', str(upper_bound - lower_bound + 1)], '<seq>']]
    else:
        rhs: RawSExprList = ['seq-concat',
            ['seq-repeat', ['range', str(lower_bound - 1), str(lower_bound - 1)], '<seq>'],
            ['seq-repeat', ['range', '1', '$'], '<seq>']]

    return (['seq-repeat', '<range>', '<seq>'], rhs)


def split_seq_repeat(container: IrContainer):
    """Breaks seq-repeat primitives up into a concatenation of two seq-repeat
    primitives as a preparation for the simple_to_automaton pass.
    Rewrite in-place in the input_container."""

    apply_rules(container, {SeqRepeat: get_split_seq_repeat_rewrite_rule})


def get_seq_repeat_to_aut_rewrite_rule(container: IrContainer, node_id: NodeId) -> RewriteRule:
    """Get the rewrite rule for the seq-repeat primitive with node_id to transform it
    into an automaton. For this, seq-repeat primitives must have been preprocessed
    with split_seq_repeat."""

    # NOTE both could be done in one step to improve efficiency by directly constructing
    # the automaton rule for the split seq-repeat

    node: PropertyIrNode = container[node_id]

    if not isinstance(node, SeqRepeat):
        raise TypeError(f'Cannot generate seq-repeat to aut-repeat rewrite rule for node {node} with wrong node type')

    repeat_range: Range = node.child1

    lower_bound: int = repeat_range.lower_bound
    upper_bound: int | Literal['$'] = repeat_range.upper_bound.value

    if lower_bound == upper_bound:
        rhs: RawSExprList = ['aut-repeat', str(upper_bound), '<seq>']

    elif lower_bound == 1 and type(upper_bound) is int:
        rhs: RawSExprList = ['aut-repeat-up-to', str(upper_bound), '<seq>']

    elif lower_bound == 1 and upper_bound == '$':
        rhs: RawSExprList = ['let-rec',
            ['start',
                ['aut-call-ex', '<seq>',
                    ['aut-or',
                        ['aut-acc', ['aut-false']],
                        ['aut-consume', ['true'], 'start', ['aut-false']]]]],
            'start']

    else:
        raise ValueError(f'Cannot generate seq-repeat to aut-repeat rewrite rule for node {node} that has not been split up')

    return (['seq-repeat', '<range>', '<seq>'], rhs)




def simple_to_automaton(input_container: IrContainer) -> IrContainer:
    """Converts the simple properties/sequence in the container into their
    automata counterparts finite automata and omega automata.
    For this, the negation normal form (nnf) must have been established and
    seq-repeat primitives must have been preprocessed with split_seq_repeat."""

    rewrite_rules: dict[type[PropertyIrNode], RewriteRule | RewriteRuleGenerator] = {

        # SEQUENCE PRIMITIVES

        SeqBool: (['seq-bool', '<bool>'],
            ['aut-read', '<bool>', ['aut-acc', ['aut-false']], ['aut-false']]),
        SeqConcat: (['seq-concat', '<seq1>', '<seq2>'],
            ['aut-call-ex', '<seq1>', ['aut-consume', ['true'], '<seq2>', ['aut-false']]]),
        SeqFusion: (['seq-fusion', '<seq1>', '<seq2>'],
            ['aut-call-ex', '<seq1>', '<seq2>']),

        SeqRepeat: get_seq_repeat_to_aut_rewrite_rule,

        SeqOr: (['seq-or', '<seq_list>'],
            ['aut-or', '<seq_list>']),
        SeqIntersect: (['seq-intersect', '<seq_list>'],
            ['aut-call-ex', ['aut-and', '<seq_list>'], ['aut-acc', 'aut-false']]),
        SeqFirstMatch: (['seq-first-match', '<seq>'],
            ['aut-call-first', '<seq>', ['aut-acc', ['aut-false']]]),

        # TODO fix this primitive and its handling in nnf rewriting
        # aut-refuted applies an automaton transformaton that happens later
        #SeqRefuted: (['seq-refuted', '<seq>'], ['aut-refuted', '<seq>']),

        SeqNoMatch: (['seq-no-match'], ['aut-false']),

        # PROPERTY PRIMITIVES

        PropStrong: (['prop-strong', '<seq>'],
            ['omega-call-ex-strong', '<seq>', ['omega-true']]),
        PropWeak: (['prop-weak', '<seq>'],
            ['omega-call-ex-weak', '<seq>', ['omega-true']]),

        PropAnd: (['prop-and', '<prop_list>'],
            ['omega-and', '<prop_list>']),
        PropOr: (['prop-or', '<prop_list>'],
            ['omega-or', '<prop_list>']),

        # prop-nexttime and prop-strong-nexttime are already unrolled at this point
        PropNexttime: (['prop-nexttime', '<int=1>', '<prop>'],
            ['omega-weak-consume', ['true'], '<prop>']),
        PropStrongNexttime: (['prop-strong-nexttime', '<int=1>', '<prop>'],
            ['omega-strong-consume', ['true'], '<prop>']),

        PropOverlappedImplication: (['prop-overlapped-implication', '<seq>', '<prop>'],
            ['omega-call-all', '<seq>', '<prop>']),
        PropOverlappedFollowedBy: (['prop-overlapped-followed-by', '<seq>', '<prop>'],
            ['omega-call-ex-strong', '<seq>', '<prop>']),

        PropUntil: (['prop-until', '<prop1>', '<prop2>'],
            ['let-rec',
                ['start',
                    ['prop-or', '<prop2>',
                        ['prop-and', '<prop1>',
                            ['omega-weak-consume-acc', ['true'], 'start', ['omega-false']]]]],
                'start']),
        PropStrongUntilWith: (['prop-strong-until-with', '<prop1>', '<prop2>'],
            ['let-rec',
                ['start',
                    ['prop-and', '<prop1>',
                        ['prop-or', '<prop2>',
                            ['omega-strong-consume', ['true'], 'start', ['omega-false']]]]],
                'start']),

        # prop-reject-on/prop-accept-on apply automaton transformatons that happen later
        PropAcceptOn: (['prop-accept-on', '<bool>', '<prop>'],
            ['omega-accept-on', '<bool>', '<prop>']),
        PropRejectOn: (['prop-reject-on', '<bool>', '<prop>'],
            ['omega-reject-on', '<bool>', '<prop>']),

    }

    # TODO handle outermost primitive for type conversion

    output_container: IrContainer = construct_rewritten_container(input_container, rewrite_rules, type_classes_to_copy = [Bool, FiniteAutomaton, OmegaAutomaton])

    return output_container
