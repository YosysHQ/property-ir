# Property IR

Intermediate representation of SVA properties.
Currently at an early stage of development.

## Prerequisites

- Install [uv](https://docs.astral.sh/uv/).

- Install [graphviz](https://graphviz.org/).

## Usage


Show help:

```
uv run prototype/src/main.py -h
```

Parse an example and generate a graph.
If the output file already exists, it will be overwritten!

```sh
uv run prototype/src/main.py examples/example_input1.pir -g output_image.png
```

Remove placeholder nodes the were generated while parsing by using the option `-b` or `--bypass`.

```sh
uv run prototype/src/main.py examples/example_input4.pir -g output_image4.png -b
```

Establish the negation normal form by using the option `-n` or `--normalform`.
The input needs to be a simple property.

```sh
uv run prototype/src/main.py examples/example_nnf1.pir -g output_image_nnf.png -n -b
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
