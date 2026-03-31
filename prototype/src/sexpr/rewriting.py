from collections import deque
import logging

from base import PropertyIrNode, PlaceholderNode, IrContainer, RawSExpr, NodeId
from sexpr.primitives import And, Not, Or



logger = logging.getLogger(__name__)



# rewrite rule example
#(seq-goto-repeat <range> <bool>)
#
#(seq-repeat <range> (seq-concat
#   (seq-repeat (range 0 $) (not <bool>))
#   <bool>))

type RewriteRule = tuple[RawSExpr, RawSExpr]

dual_primitives: dict[type[PropertyIrNode], type[PropertyIrNode]] = {
    And: Or,
    Or: And
}

negation_primitives: set[type[PropertyIrNode]] = {Not}



def apply_rules(container: IrContainer, rules: list[RewriteRule]):
    """Perform a single pass through the expression graph in the container
    and create a new graph that results when at each node applying a rewrite
    rule if there is a matching one."""
    pass



def reduce_primitives(container: IrContainer):
    """Replace all primitives that do not exist in simple sequences and simple
    properties."""
    pass



def rewrite_clocks(container: IrContainer):
    """Rewrite the expression graph such that the global clock is used."""
    pass




def nnf_process_node(
    node_id: NodeId,
    invert: bool,
    output_container: IrContainer,
    corresponding_nodes: dict[NodeId, NodeId],
    polarity_changed: dict[NodeId, bool]):
    """Recursive function to process a node and all nodes reachable from it,
    to create corresponding expression graph in negation normal form.
    Bool parameter invert states whether the input node needs to change polarity."""

    pass




def nnf(container: IrContainer) -> IrContainer:
    """Create a new expression graph that is the negation normal form of the
    graph stored in the container. If there are cycles with an odd number of
    negations, this results in an error. Cycles with an even number of negations
    are acceptable."""

    # depth-first search through expression graph
    # start recursion at all nodes with global names or unnamed roots (source + inner + sink nodes)
    # (if at that point they are not yet finished through another recursive function call)

    # keep track in dict of input nodes and corresponding output nodes
    # other dict keeps track of if the polarity of an input node has been changed for odd loop detection

    # for each node, call a recursive helper function that does the following
    # hand down the dicts to keep track of visited nodes and polarity changes, and the output container

    # if already existent and handled, return stored node from dict
    # if polarity is conflicting, there is a cycle with an odd number of negations, raise exception
    # if leaf, directly create and store and return node (might be necessary to create negation here)
    # else create PlaceholderNode for current node and put into dict
    # set type of placeholder to expected type, depending on polarity

    # call recursion for children, with correct polarity
    # obtain child node ids
    # instantiate current placeholder node and set its children

    # keep global node names of input nodes and transfer to output nodes
    # if negation has global name, move to child node

    # set source, inner, sink nodes sets of output container accordingly


    output_container: IrContainer = IrContainer()
    invert: bool = False
    corresponding_nodes: dict[NodeId, NodeId] = dict()
    polarity_changed: dict[NodeId, bool] = dict()

    nodes_to_process: deque[NodeId] = deque(container.source_nodes.values())
    nodes_to_process += container.inner_nodes.values()
    nodes_to_process += container.sink_nodes

    visited: set[NodeId] = set()

    while len(nodes_to_process) > 0:
        current_id: NodeId = nodes_to_process.popleft()

        nnf_process_node(current_id, invert, output_container, corresponding_nodes, polarity_changed)


    return output_container