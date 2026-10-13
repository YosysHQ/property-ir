#ifndef YOSYS_PROPERTY_IR_EMITTER_H
#define YOSYS_PROPERTY_IR_EMITTER_H

#include "property_ir/sexpr_printer.h"

#include <initializer_list>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

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
  explicit IntLiteral() = delete;
};

struct RangeLiteral {
  explicit RangeLiteral() = delete;
};

struct BoundedRangeLiteral {
  explicit BoundedRangeLiteral() = delete;
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
