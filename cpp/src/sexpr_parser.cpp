#include "property_ir/sexpr_parser.h"
#include "sexpr_common.h"

#include <cassert>

namespace property_ir {
namespace {

bool is_whitespace(char c) {
  return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' ||
         c == '\v';
}

} // namespace

SExprParser::SExprParser(std::string_view input) : input(input) {}

const SExprParser::Result &SExprParser::peek() {
  assert(!past_end);
  if (!current)
    current = read();
  return *current;
}

void SExprParser::advance() {
  const auto *token = std::get_if<SExprToken>(&peek());
  if (!token)
    return;
  past_end = token->kind == SExprToken::Kind::End;
  current.reset();
}

SExprParser::Result SExprParser::next() {
  auto result = peek();
  advance();
  return result;
}

SExprParser::Result SExprParser::read() {
  while (position < input.size() && is_whitespace(input[position]))
    ++position;

  if (position == input.size()) {
    if (depth != 0)
      return SExprParseError{position, "Unclosed list at end of input"};
    return SExprToken{SExprToken::Kind::End, {}, position};
  }

  const auto start = position;
  if (input[position] == '(') {
    ++position;
    ++depth;
    return SExprToken{SExprToken::Kind::BeginList, input.substr(start, 1),
                      start};
  }
  if (input[position] == ')') {
    if (depth == 0)
      return SExprParseError{position, "Unexpected closing parenthesis"};
    ++position;
    --depth;
    return SExprToken{SExprToken::Kind::EndList, input.substr(start, 1), start};
  }

  while (position < input.size()) {
    const char c = input[position];
    if (is_whitespace(c) || c == '(' || c == ')')
      break;
    if (!is_atom_char(c))
      return SExprParseError{position, "Invalid character in atom"};
    ++position;
  }
  return SExprToken{SExprToken::Kind::Atom,
                    input.substr(start, position - start), start};
}

} // namespace property_ir
