#ifndef YOSYS_PROPERTY_IR_SEXPR_PARSER_H
#define YOSYS_PROPERTY_IR_SEXPR_PARSER_H

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <variant>

namespace property_ir {

struct SExprToken {
  enum class Kind { BeginList, EndList, Atom, End };

  Kind kind;
  std::string_view text;
  std::size_t offset;
};

struct SExprParseError {
  std::size_t offset;
  std::string message;
};

class SExprParser {
public:
  using Result = std::variant<SExprToken, SExprParseError>;

  explicit SExprParser(std::string_view input);

  // Returns the current token or error without consuming it. The reference is
  // valid until `advance()`. Asserts if `End` has already been consumed.
  const Result &peek();

  // Consumes the current token. Does nothing once a parse error is reached.
  // Asserts if `End` has already been consumed.
  void advance();

  // Copies `peek()`'s result, calls `advance()`, and returns the copy.
  Result next();

private:
  Result read();

  std::string_view input;
  std::size_t position = 0;
  std::size_t depth = 0;
  std::optional<Result> current;
  bool past_end = false;
};

} // namespace property_ir

#endif
