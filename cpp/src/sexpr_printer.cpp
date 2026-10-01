#include "property_ir/sexpr_printer.h"

#include <algorithm>
#include <cassert>
#include <ostream>

namespace property_ir {

SExprPrinter::SExprPrinter(std::ostream &output) : output(output) {}

void SExprPrinter::indent() {
  if (!at_line_start)
    return;
  for (std::size_t i = 1; i < scopes.size(); ++i)
    output << "  ";
  at_line_start = false;
}

void SExprPrinter::begin_element() {
  if (scopes.back().lines && !at_line_start)
    line();
  if (at_line_start)
    indent();
  else if (!scopes.back().first)
    output.put(' ');
  scopes.back().first = false;
}

void SExprPrinter::begin_list() {
  begin_element();
  output.put('(');
  scopes.push_back(Scope{true, scopes.back().compact});
}

void SExprPrinter::end_list() {
  assert(scopes.size() > 1);
  if (scopes.back().lines && !at_line_start)
    line();
  scopes.pop_back();
  indent();
  output.put(')');
}

void SExprPrinter::raw_atom(std::string_view text) {
  begin_element();
  output << text;
}

void SExprPrinter::identifier(std::string_view text) {
  assert(!text.empty());
  assert(std::all_of(text.begin(), text.end(), [](char c) {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
           (c >= '0' && c <= '9') || c == '_' || c == '$' || c == ':' ||
           c == '-';
  }));
  raw_atom(text);
}

void SExprPrinter::line() {
  if (scopes.back().compact)
    return;
  output.put('\n');
  at_line_start = true;
}

void SExprPrinter::compact() {
  scopes.back().compact = true;
  scopes.back().lines = false;
}

void SExprPrinter::lines() {
  if (!scopes.back().compact)
    scopes.back().lines = true;
}

} // namespace property_ir
