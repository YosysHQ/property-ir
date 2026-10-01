#ifndef YOSYS_PROPERTY_IR_SEXPR_PRINTER_H
#define YOSYS_PROPERTY_IR_SEXPR_PRINTER_H

#include <iosfwd>
#include <string_view>
#include <utility>
#include <vector>

namespace property_ir {

class SExprPrinter {
public:
  explicit SExprPrinter(std::ostream &output);

  // Elements are automatically separated by whitespace.
  void begin_list();
  // Must match a previous begin_list().
  void end_list();

  template <typename F> void list(F &&body) {
    begin_list();
    std::forward<F>(body)();
    end_list();
  }

  // Writes text unchanged without any escaping, quoting or validation.
  void raw_atom(std::string_view text);

  // Writes an identifier.
  // Asserts that the identifer name can be represented.
  void identifier(std::string_view text);

  // Writes a newline if not in compact mode. Automatically indents the next
  // line.
  void line();

  // Enters compact mode and restores the previous mode when the current list
  // is closed.
  void compact();

  // Enters multi-line mode which starts each element and the closing
  // parenthesis on a new line. Does not apply to nested lists and is ignored
  // if already in compact mode.
  void lines();

private:
  struct Scope {
    bool first = true;
    bool compact = false;
    bool lines = false;
  };

  void begin_element();
  void indent();

  std::ostream &output;
  // The first scope applies to top-level items not part of any list.
  std::vector<Scope> scopes = {Scope{}};
  bool at_line_start = true;
};

} // namespace property_ir

#endif
