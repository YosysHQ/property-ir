from pygments.lexer import RegexLexer
from pygments.token import Keyword, Comment, Name, Punctuation, String, Number, Text, Whitespace, Operator

class SExprLexer(RegexLexer):
    name = "SExpr"
    aliases = ["sexpr", "pir"]
    filenames = ["*.sexpr", "*.pir"]

    tokens = {
        'root' : [
            (r'[()]', Punctuation),
            (r'[\[\]]', String),
            (r'\b(let-rec|declare-rec|declare-input|declare)\b', Keyword),
            (r'\b((assert|cover|assume|restrict)\-property)|(cover\-sequence)\b', Keyword),
            (r'\;.*', Comment),
            (r'(<[a-zA-Z0-9_\-]+>)', String),
            (r'\b([0-9]+|true|false|range|bounded\-range)\b', Number),
            (r'\$', Number),
            (r'\#[a-z\-]+', String),
            (r'\b(not|or|and|constant)\b', Name.Tag),
            (r'\b((prop\-|seq\-|bool\-|clk\-prop\-|clk\-seq\-|state\-)[a-z\-]+)\b', Name.Tag),
            (r'\s+', Whitespace),
            (r'.', Text)
        ]
    }
