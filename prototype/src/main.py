from __future__ import annotations
import argparse
from pathlib import Path
import logging

from sexpr import parse_expression, parse_raw_sexpr, IrContainer, Signal, RawSExprList, unparse_raw_sexpr, parse_document
from sexpr.base import SignalDeclaration


logger = logging.getLogger(__name__)


def main():

    parser = argparse.ArgumentParser(description='Parse and process Property IR documents')

    parser.add_argument('input', help='Property IR text document')
    parser.add_argument('-o', '--output', help='generate Property IR output document and write to file')
    parser.add_argument('-i', '--image', help='generate expression graph image and write to file')
    parser.add_argument('-b', '--bypass', help='bypass placeholder nodes', action='store_true')
    parser.add_argument('-v', '--verbose', help='show debug messages', action='store_true')

    args = parser.parse_args()


    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    with open(args.input, 'r') as file:
        input_document: str = file.read()

    raw_sexpr: RawSExprList = parse_raw_sexpr(input_document)
    ir_container = IrContainer()
    root_node_id = parse_document(raw_sexpr, ir_container)

    if args.bypass:
        ir_container.bypass_placeholders()

    output_raw_sexpr = ir_container.output_container()
    output_unparsed = unparse_raw_sexpr(output_raw_sexpr)

    logger.info(output_raw_sexpr)
    logger.info(output_unparsed)

    if args.output:
        with open(args.output, 'w') as file:
            file.write(output_unparsed)

    if args.image:
        ir_container.show_graph(Path(args.image))


if __name__ == "__main__":

    main()
