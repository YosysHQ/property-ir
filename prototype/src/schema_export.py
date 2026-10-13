"""Exports Property IR signatures as JSON for code generation."""

# The schema is {"types": <type-list>, "primitives": <primitive-list>, "statements": <statement-list>}.
#
# Types are represented as {"name": <type-name>, "kind": <kind>}.
# The kinds are "expression", "literal" or "enum", with enums having an extra "values": <string-list> field.
# Primitives are represented as {"name": <string>, "result": <type-name>, "arguments": <argument-list>}.
# Statements are represented as {"name": <string>, "arguments": <argument-list>, "options": <option-list>}.
# Arguments are represented as {"name": <string>, "type": <type-name>, "variadic": <boolean>}.
# Options are represented as {"name": <string>, "keyword": <string>, "type": <type-name>, "default": <value>}.

import json
from dataclasses import MISSING, fields
from enum import Enum
from types import UnionType
from typing import get_args, get_origin, get_type_hints

from ir.base import (
    Bool,
    BoundedRange,
    ClockedProperty,
    ClockedSequence,
    Directive,
    EvaluationScope,
    FiniteAutomaton,
    NodeId,
    OmegaAutomaton,
    Property,
    PropertyIrNode,
    PropertyType,
    Range,
    RootTestDirective,
    Sequence,
    Signal,
    VacuityMode,
)
from ir.parsing import name_to_directive, op_to_cls

EXPRESSION_TYPES = {
    Bool: "bool",
    ClockedSequence: "clk-seq",
    ClockedProperty: "clk-prop",
    Sequence: "seq",
    Property: "prop",
    FiniteAutomaton: "aut",
    OmegaAutomaton: "omega",
}

LITERAL_TYPES = {
    bool: "bool-literal",
    int: "int",
    Range: "range",
    BoundedRange: "bounded-range",
}

ENUM_TYPES = {
    PropertyType: "property-type",
    EvaluationScope: "evaluation-scope",
    VacuityMode: "vacuity-mode",
}

TYPE_NAMES = EXPRESSION_TYPES | LITERAL_TYPES | ENUM_TYPES


def type_name(annotation):
    """Returns the schema type name, unwrapping NodeId[T]."""
    if get_origin(annotation) is NodeId:
        (annotation,) = get_args(annotation)
    try:
        return TYPE_NAMES[annotation]
    except KeyError:
        raise TypeError(f"Unsupported schema type: {annotation!r}") from None


def export_argument(name, annotation):
    """Describes a positional argument, treating lists as variadic."""
    variadic = get_origin(annotation) is list
    if variadic:
        (annotation,) = get_args(annotation)
    return {
        "name": name,
        "type": type_name(annotation),
        "variadic": variadic,
    }


def export_primitive(cls: type[PropertyIrNode]):
    """Exports a primitive's signature."""
    return {
        "name": cls.op_symbol(),
        "result": type_name(cls.type_class()),
        "arguments": [
            export_argument(field.name, annotation)
            for field, annotation in zip(
                cls.get_child_fields(), cls.signature(), strict=True
            )
        ],
    }


def export_directive(cls: type[Directive]):
    """Exports a directive's signature."""
    hints = get_type_hints(cls)
    options = []
    for field in fields(cls):
        if field.name == "node_id":
            # exported separately below.
            continue
        annotation = hints[field.name]
        if get_origin(annotation) is UnionType:
            members = get_args(annotation)
            if len(members) != 2 or type(None) not in members:
                raise TypeError(f"Unsupported option type: {annotation!r}")
            annotation = next(member for member in members if member is not type(None))
        default = field.default
        if default is MISSING:
            raise TypeError(f"Missing option default: {cls.__name__}.{field.name}")
        if isinstance(default, Enum):
            default = default.value
        options.append(
            {
                "name": field.name,
                "keyword": ":" + field.name.replace("_", "-"),
                "type": type_name(annotation),
                "default": default,
            }
        )
    return {
        "name": cls.op_symbol(),
        "arguments": [  # same for all directives
            export_argument("node_id", cls.node_type())
        ],
        "options": options,
    }


def export_schema():
    types = (
        [{"name": name, "kind": "expression"} for name in EXPRESSION_TYPES.values()]
        + [{"name": name, "kind": "literal"} for name in LITERAL_TYPES.values()]
        + [
            {"name": name, "kind": "enum", "values": [member.value for member in cls]}
            for cls, name in ENUM_TYPES.items()
        ]
    )
    return {
        "types": types,
        "primitives": [
            export_primitive(cls)
            for _, cls in sorted(op_to_cls.items())
            if cls is not Signal
        ],
        "statements": [
            export_directive(cls)
            for _, cls in sorted(name_to_directive.items())
            if cls is not RootTestDirective
        ],
    }


if __name__ == "__main__":
    print(json.dumps(export_schema(), indent=2))
