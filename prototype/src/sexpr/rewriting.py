from collections import deque
import logging

from sexpr.base import PropertyIrNode, PlaceholderNode, IrContainer, RawSExpr, NodeId, Signal
from sexpr.primitives import And, Constant, Not, Or



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
    container: IrContainer,
    invert: bool,
    output_container: IrContainer,
    corresponding_nodes: dict[NodeId, NodeId],
    polarity_changed: dict[NodeId, bool]):
    """Recursive function to process a node and all nodes reachablgge from it,
    to create corresponding expression graph in negation normal form.
    Bool parameter invert states whether the input node needs to change polarity."""

    current_node = container[node_id]

    # signals themselves can never be inside a cycle because they are leaves
    # and we do not store their polarity because they can be encountered multiple times
    # but that can happen with every named node in a DAG! that is perfectly legel even if polarity changes
    # instead keep track of nodes in current recursion stack, which shows when there is a cycle and not just a shared subgraph
    if isinstance(current_node, Signal):
        if not invert:
            return corresponding_nodes[node_id]
        else:
            container.add_node_by_kwargs(Not, {'child': corresponding_nodes[node_id]})


    # if already existent and handled, return stored node from dict
    # if polarity is conflicting, there is a cycle with an odd number of negations, raise exception
    if node_id in corresponding_nodes:
        if polarity_changed[node_id] and invert:
            raise ValueError('Cycle with odd number of negations detected at node %s', container[node_id])
        else:
            return corresponding_nodes[node_id]




    # if non-signal leaf, directly create and store and return node (might be necessary to create negation here)
    elif isinstance(current_node, Constant):
        pass



    # else create PlaceholderNode for current node and put into dict
    # set type of placeholder to expected type, depending on polarity

    # call recursion for children, with correct polarity
    # obtain child node ids
    # instantiate current placeholder node and set its children

    # keep global node names of input nodes and transfer to output nodes
    # if negation has global name, move to child node




def nnf(container: IrContainer) -> IrContainer:
    """Create a new expression graph that is the negation normal form of the
    graph stored in the container. If there are cycles with an odd number of
    negations, this results in an error. Cycles with an even number of negations
    are acceptable."""

    output_container: IrContainer = IrContainer()
    invert: bool = False

    corresponding_nodes: dict[NodeId, NodeId] = dict() # input nodes and corresponding output nodes
    polarity_changed: dict[NodeId, bool] = dict() # keeps track if the polarity of an input node has been changed for odd loop detection

    # add signals to output container = set source nodes and their names
    for name, node_id in container.source_nodes.items():
        signal_node = output_container.add_signal_node(name)
        corresponding_nodes[node_id] = signal_node.node_id
        output_container.global_nodes[name] = signal_node.node_id
        output_container.node_names[name] = signal_node.node_id

    # depth-first search through expression graph
    # start recursion at all nodes with global names or unnamed roots (source + inner + sink nodes)
    # (if at that point they are not yet finished through another recursive function call)

    nodes_to_process: deque[NodeId] = deque(container.source_nodes.values())
    nodes_to_process += container.inner_nodes.values()
    nodes_to_process += container.sink_nodes

    visited: set[NodeId] = set()

    while len(nodes_to_process) > 0:

        # for each node, call recursive helper function
        # hand down the dicts to keep track of visited nodes and polarity changes, and the output container

        current_id: NodeId = nodes_to_process.popleft()

        logger.debug('nnf rewriting process node %s', container[current_id])

        nnf_process_node(current_id, container, invert, output_container, corresponding_nodes, polarity_changed)


    # TODO set inner and sink nodes sets of output container accordingly

    return output_container