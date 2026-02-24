from sphinx.application import Sphinx
from sexpr_lexer import SExprLexer

def setup(app: Sphinx) -> None:
    app.add_lexer("sexpr", SExprLexer)