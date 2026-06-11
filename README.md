# Property IR

Intermediate representation of SVA properties.
Early stage development at the moment.

## Prerequisites

- Install [uv](https://docs.astral.sh/uv/).

- Install [graphviz](https://graphviz.org/).

## Usage


Show help:

```
uv run prototype/src/main.py -h
```

Parse an example and generate a graph (opens with graphviz).
If the output file already exists, it will be overwritten!

```sh
uv run prototype/src/main.py examples/example_input1.pir -g ./output_image.png
```

Run the tests:

```sh
uv run pytest
```

## Specification

The Property IR specification can be found online [here](https://yosyshq.readthedocs.io/projects/property-ir/en/latest/index.html).

Building the specification:

```sh
uv run sphinx-build -b html spec/source/ spec/build/html
```
