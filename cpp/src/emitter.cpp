#include "property_ir/emitter.h"

#include <cstdlib>
#include <tuple>

namespace property_ir {
namespace detail {

namespace {

template <typename F> struct CallableEmitter : Emitter {
  explicit CallableEmitter(F body) : body(std::move(body)) {}

  void emit(SExprPrinter &printer) const override { body(printer); }

  F body;
};

template <typename F> EmitterPtr make_emitter(F body) {
  return std::make_shared<CallableEmitter<F>>(std::move(body));
}

template <typename T>
void emit_argument(SExprPrinter &printer, const T &value) {
  property_ir::emit(printer, value);
}

void emit_argument(SExprPrinter &printer, bool value) {
  printer.identifier(value ? "true" : "false");
}

void emit_argument(SExprPrinter &printer, int value) {
  printer.identifier(std::to_string(value));
}

void emit_argument(SExprPrinter &printer, std::optional<int> value) {
  printer.identifier(value.has_value() ? std::to_string(value.value()) : "$");
}

void emit_argument(SExprPrinter &printer, IntLiteral value) {
  emit_argument(printer, value.value);
}

void emit_argument(SExprPrinter &printer, RangeLiteral range) {
  printer.list([&] {
    printer.identifier("range");
    emit_argument(printer, range.lower);
    emit_argument(printer, range.upper);
  });
}

void emit_argument(SExprPrinter &printer, BoundedRangeLiteral range) {
  printer.list([&] {
    printer.identifier("bounded-range");
    emit_argument(printer, range.lower);
    emit_argument(printer, range.upper);
  });
}

template <typename T>
void emit_argument(SExprPrinter &printer, const std::vector<T> &values) {
  for (const auto &value : values)
    emit_argument(printer, value);
}

} // namespace

EmitterPtr identifier(std::string name) {
  return make_emitter([name = std::move(name)](SExprPrinter &printer) {
    printer.identifier(name);
  });
}

template <typename T, typename... Args>
T application(const char *name, Args... args) {
  return T(make_emitter([name, args = std::make_tuple(std::move(args)...)](
                            SExprPrinter &printer) {
    printer.list([&] {
      printer.identifier(name);
      std::apply(
          [&](const auto &...arg) { (emit_argument(printer, arg), ...); },
          args);
    });
  }));
}

} // namespace detail

Statement declare_input(BoolId name) {
  return detail::application<Statement>("declare-input", std::move(name));
}

template <Type T> Statement declare(Identifier<T> name, Expr<T> value) {
  return detail::application<Statement>("declare", std::move(name),
                                        std::move(value));
}

void emit(SExprPrinter &printer, const Statement &statement) {
  statement.emitter->emit(printer);
}

#include "property_ir/emitter_definitions.inc"

} // namespace property_ir
