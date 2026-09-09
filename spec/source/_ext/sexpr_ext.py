from sexpr_lexer import SExprLexer
from sphinx.application import Sphinx


def setup(app: Sphinx) -> None:
    app.add_lexer("sexpr", SExprLexer)
