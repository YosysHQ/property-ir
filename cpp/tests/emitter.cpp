#include "property_ir/emitter.h"

#include <gtest/gtest.h>
#include <sstream>

namespace property_ir {
namespace {

class EmitterTest : public testing::Test {
protected:
  std::ostringstream output;
  SExprPrinter printer{output};
};

// spec/source/types.rst: Boolean Expressions
TEST_F(EmitterTest, BooleanExpressions) {
  BoolId a("a");
  BoolId b("b");
  BoolId c("c");

  printer.lines();

  emit(printer, declare_input(a));
  emit(printer, declare_input(b));
  emit(printer,
       declare(c, bool_and(bool_or(a, b), bool_not(b), constant(true))));

  printer.line();

  EXPECT_EQ("(declare-input a)\n"
            "(declare-input b)\n"
            "(declare c (and (or a b) (not b) (constant true)))\n",
            output.str());
}

// spec/source/introduction.rst: General Concept
TEST_F(EmitterTest, SequenceImplication) {
  BoolId a("a");
  BoolId b("b");
  BoolId c("c");
  ClkPropId p("p");

  emit(printer, declare(p, clk_prop_overlapped_implication(
                               clk_seq_concat(clk_seq_bool(a), clk_seq_bool(b)),
                               clk_prop_always(clk_prop_bool(c)))));

  EXPECT_EQ("(declare p (clk-prop-overlapped-implication "
            "(clk-seq-concat (clk-seq-bool a) (clk-seq-bool b)) "
            "(clk-prop-always (clk-prop-bool c))))",
            output.str());
}

} // namespace
} // namespace property_ir
