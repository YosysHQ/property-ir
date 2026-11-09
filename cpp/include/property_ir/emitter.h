#ifndef YOSYS_PROPERTY_IR_EMITTER_H
#define YOSYS_PROPERTY_IR_EMITTER_H

#include "property_ir/sexpr_printer.h"

#include <initializer_list>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>
#include <stdexcept>
#include <optional>
#include <limits>

namespace property_ir {

namespace detail {
struct Emitter {
  virtual ~Emitter() = default;
  virtual void emit(SExprPrinter &printer) const = 0;
};

using EmitterPtr = std::shared_ptr<const Emitter>;

EmitterPtr identifier(std::string name);
} // namespace detail

enum class Type;

struct IntLiteral {
  const int value;

  IntLiteral(int value) : value{value} {
    if (value < 0)
      throw std::invalid_argument("invalid range");
  }
};

struct RangeLiteral {
  const int lower;
  const std::optional<int> upper;

  RangeLiteral(int lower, std::optional<int> upper = std::nullopt) : lower{lower}, upper{upper} {

    if (lower < 0 || upper.value_or(std::numeric_limits<int>::max()) < lower)
      throw std::invalid_argument("invalid range");
  }

  bool single() const { return upper.has_value() && lower == upper; }
  bool single(int test) const { return single() && lower == test; }
  bool unbounded() const { return !upper.has_value(); }
};

struct BoundedRangeLiteral {
  const int lower;
  const int upper;

  BoundedRangeLiteral(int lower, int upper) : lower{lower}, upper{upper} {
    if (lower < 0 || upper < lower)
      throw std::invalid_argument("invalid bounded range");
  }

  bool single() const { return lower == upper; }
  bool single(int test) const { return single() && lower == test; }
};

template <Type T> class Identifier;

template <Type T> class Expr {
public:
  explicit Expr(detail::EmitterPtr emitter) : emitter(std::move(emitter)) {}

private:
  detail::EmitterPtr emitter;

  template <Type U> friend void emit(SExprPrinter &, const Expr<U> &);
};

template <Type T> void emit(SExprPrinter &printer, const Expr<T> &expression) {
  expression.emitter->emit(printer);
}

template <Type T> class Identifier {
public:
  explicit Identifier(std::string name)
      : expression(detail::identifier(std::move(name))) {}

  operator Expr<T>() const { return expression; }

private:
  Expr<T> expression;

  template <Type U> friend void emit(SExprPrinter &, const Identifier<U> &);
};

template <Type T>
void emit(SExprPrinter &printer, const Identifier<T> &identifier) {
  emit(printer, identifier.expression);
}

class Statement {
public:
  explicit Statement(detail::EmitterPtr emitter)
      : emitter(std::move(emitter)) {}

  friend void emit(SExprPrinter &printer, const Statement &statement);

private:
  detail::EmitterPtr emitter;
};

#include "property_ir/emitter_declarations.inc"

Statement declare_input(BoolId name);

template <Type T> Statement declare(Identifier<T> name, Expr<T> value);

template <Type T> Statement declare(Identifier<T> name, Identifier<T> value) {
  return declare(std::move(name), Expr<T>(value));
}

void emit(SExprPrinter &printer, const Statement &statement);

} // namespace property_ir

#endif
