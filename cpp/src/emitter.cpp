#include "property_ir/emitter.h"

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
          [&](const auto &...arg) { (property_ir::emit(printer, arg), ...); },
          args);
    });
  }));
}

} // namespace detail

BoolExpr constant(bool value) {
  return BoolExpr(detail::make_emitter([value](SExprPrinter &printer) {
    printer.list([&] {
      printer.raw_atom("constant");
      printer.raw_atom(value ? "true" : "false");
    });
  }));
}

ClkPropExpr clk_prop_bool(BoolExpr value) {
  return detail::application<ClkPropExpr>("clk-prop-bool", std::move(value));
}

ClkPropExpr clk_prop_always(ClkPropExpr property) {
  return detail::application<ClkPropExpr>("clk-prop-always",
                                          std::move(property));
}

ClkPropExpr clk_prop_and(std::vector<ClkPropExpr> properties) {
  return ClkPropExpr(detail::make_emitter(
      [properties = std::move(properties)](SExprPrinter &printer) {
        printer.list([&] {
          printer.raw_atom("clk-prop-and");
          for (const auto &property : properties)
            property_ir::emit(printer, property);
        });
      }));
}

ClkPropExpr clk_prop_and(std::initializer_list<ClkPropExpr> properties) {
  return clk_prop_and(std::vector<ClkPropExpr>(properties));
}

Statement declare_input(BoolId name) {
  return detail::application<Statement>("declare-input", std::move(name));
}

template <Type T> Statement declare(Identifier<T> name, Expr<T> value) {
  return detail::application<Statement>("declare", std::move(name),
                                        std::move(value));
}

template Statement declare(BoolId name, BoolExpr value);
template Statement declare(ClkPropId name, ClkPropExpr value);

void emit(SExprPrinter &printer, const Statement &statement) {
  statement.emitter->emit(printer);
}

} // namespace property_ir
