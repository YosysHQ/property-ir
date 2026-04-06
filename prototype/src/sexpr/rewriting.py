from collections import deque
from typing import get_origin, Any
import logging

from sexpr.base import PropertyIrNode, PlaceholderNode, IrContainer, RawSExpr, NodeId, Signal, LiteralType
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
    corresponding_nodes: dict[tuple[NodeId, bool], NodeId],
    nodes_in_call_stack: set[tuple[NodeId, bool]]) -> NodeId:
    """Recursive function to process a node and all nodes reachablgge from it,
    to create corresponding expression graph in negation normal form.
    Bool parameter invert states whether the input node needs to change polarity."""


    # dicts should store representatives
    repr_id = container.merged_nodes.find(node_id)
    current_node = container[repr_id]

    logger.debug('--- nnf_process_node ---')
    logger.debug('Nodes in call stack: %s', nodes_in_call_stack)
    logger.debug('Current node: %s', current_node)
    logger.debug('Invert: %s', invert)

    # if same node is reached again in same call with conflicting polarity, cycle with odd number of negations detected
    if (repr_id, not invert) in nodes_in_call_stack:
        raise ValueError('Cycle with odd number of negations detected at node %s', container[repr_id])

    # if already existent and handled, return stored node from dict
    if (repr_id, invert) in corresponding_nodes:
        return corresponding_nodes[(repr_id, invert)]

    # generate output nodes for leaf cases

    if isinstance(current_node, Signal):
        if invert:
            added_node = output_container.add_node_by_kwargs(Not, {'child': corresponding_nodes[(repr_id, False)]})
            corresponding_nodes[(repr_id, True)] = added_node.node_id
            logger.debug('Added Not node: %s', added_node.node_id)
            return added_node.node_id
        else:
            raise ValueError('Signal with node id %s is missing in corresponding_nodes', repr_id)

    elif isinstance(current_node, Constant):
        new_value = current_node.value if not invert else not current_node.value
        added_node = output_container.add_node_by_kwargs(Constant, {'value': new_value})
        corresponding_nodes[(repr_id, invert)] = added_node.node_id
        logger.debug('Added Constant node: %s', added_node.node_id)
        return added_node.node_id

    # add current node to recursion stack
    # which detects when there is a cycle and not just a shared subgraph
    nodes_in_call_stack.add((repr_id, invert))

    # handle negation, which does not cause a primitive to be generated, but only invokes a subcall with flipped polarity
    if isinstance(current_node, Not):
        placeholder_node = output_container.add_placeholder_node()
        corresponding_nodes[(repr_id, invert)] = placeholder_node.node_id
        logger.debug('Added placeholder node: %s', placeholder_node.node_id)
        result_id = nnf_process_node(current_node.child, container, not invert, output_container, corresponding_nodes, nodes_in_call_stack)
        logger.debug('Output container nodes %s', output_container.nodes)
        placeholder_node.instantiate_placeholder(output_container[result_id])
        logger.debug('Instantiated placeholder node %s with %s', placeholder_node.node_id, result_id)
        nodes_in_call_stack.remove((repr_id, invert))
        return result_id

    # generate output nodes for other non-leaf cases

    # create PlaceholderNode for current node and put into dict
    # set type of placeholder to expected type, depending on polarity
    new_primitive_type = type(current_node) if not invert else dual_primitives[type(current_node)]
    placeholder_node = output_container.add_placeholder_node(expected_type=new_primitive_type)
    corresponding_nodes[(repr_id, invert)] = placeholder_node.node_id
    logger.debug('Added placeholder node: %s', placeholder_node.node_id)

    # call recursion for all non-literal children, with correct polarity
    # obtain child node ids

    signature = type(current_node).signature()
    kwargs: dict[str, Any] = {}

    for index, field in enumerate(current_node.get_child_fields()):
        field_type: type = signature[index]
        if get_origin(field_type) is list:
            list_elems = getattr(current_node, field.name)
            output_child_list = []
            for child_id in list_elems:
                output_child_id = nnf_process_node(child_id, container, invert, output_container, corresponding_nodes, nodes_in_call_stack)
                output_child_list.append(output_child_id)
            kwargs[field.name] = output_child_list

        elif issubclass(field_type, PropertyIrNode):
            child_id = getattr(current_node, field.name)
            output_child_id = nnf_process_node(child_id, container, invert, output_container, corresponding_nodes, nodes_in_call_stack)
            kwargs[field.name] = output_child_id

        elif issubclass(field_type, LiteralType.__value__):
            child_literal = getattr(current_node, field.name)
            kwargs[field.name] = child_literal

    # instantiate current placeholder node and set its children
    new_node = output_container.add_node_by_kwargs(new_primitive_type, kwargs)
    placeholder_node.instantiate_placeholder(new_node)
    logger.debug('Instantiated placeholder node %s with %s', placeholder_node.node_id, new_node.node_id)

    # remove current node from call stack
    nodes_in_call_stack.remove((repr_id, invert))

    return placeholder_node.node_id




def nnf(container: IrContainer) -> IrContainer:
    """Create a new expression graph that is the negation normal form of the
    graph stored in the container. If there are cycles with an odd number of
    negations, this results in an error. Cycles with an even number of negations
    are acceptable."""

    output_container: IrContainer = IrContainer()

    corresponding_nodes: dict[tuple[NodeId, bool], NodeId] = dict() # input nodes and corresponding output nodes
    polarity_changed: dict[NodeId, bool] = dict() # keeps track if the polarity of an input node has been changed for odd loop detection

    # add signals to output container = set source nodes and their names
    for name, node_id in container.source_nodes.items():
        signal_repr_id = container.merged_nodes.find(node_id)
        signal_node = output_container.add_signal_node(name)
        corresponding_nodes[(signal_repr_id, False)] = signal_node.node_id
        logger.debug('Added Signal node %s', signal_node)
        output_container.global_nodes[name] = signal_node.node_id
        output_container.node_names[name] = signal_node.node_id
        output_container.sink_nodes.append(signal_node.node_id)

    # depth-first search through expression graph
    # start recursion at unnamed roots (sink nodes), which will later be those used directly in assertion statements
    nodes_to_process: deque[NodeId] = deque(container.sink_nodes)

    while len(nodes_to_process) > 0:

        # for each node, call recursive helper function
        # hand down the dicts to keep track of visited nodes and polarity changes, and the output container

        current_id: NodeId = nodes_to_process.popleft()

        # if the node is already finished with positive polarity through another recursive function call, skip it
        if (current_id, True) in corresponding_nodes:
            continue

        logger.debug('nnf rewriting process node %s', container[current_id])

        # start with empty set as recursion stack
        output_node_id = nnf_process_node(current_id, container, False, output_container, corresponding_nodes, set())

        # add to sink nodes of output container because it corresponds to an unnamed rooot
        output_container.sink_nodes.append(output_node_id)


    # TODO set inner nodes of output container accordingly

    # TODO: keep global node names of input nodes and transfer to output nodes
    # if negated node, add negation indicator to node label
    # if negation has global name, move to child node

    return output_container
