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

// spec/source/types.rst: Literal types
TEST_F(EmitterTest, LiteralTypes) {
  BoolId b("b");
  ClkPropId p("p");
  ClkPropId q("q");
  ClkSeqId r("r");
  ClkSeqId s("s");
  ClkSeqId t("t");

  printer.lines();

  emit(printer, declare_input(b));
  emit(printer, declare(p, clk_prop_nexttime(2, clk_prop_bool(b))));
  emit(printer, declare(q, clk_prop_eventually(BoundedRangeLiteral(3, 5), clk_prop_bool(b))));
  emit(printer, declare(r, clk_seq_delay({2, 4}, clk_seq_bool(b))));
  emit(printer, declare(s, clk_seq_delay({2}, clk_seq_bool(b))));
  emit(printer, declare(t, clk_seq_delay({2, 2}, clk_seq_bool(b))));

  printer.line();

  EXPECT_EQ("(declare-input b)\n"
            "(declare p (clk-prop-nexttime 2 (clk-prop-bool b)))\n"
            "(declare q (clk-prop-eventually (bounded-range 3 5) (clk-prop-bool b)))\n"
            "(declare r (clk-seq-delay (range 2 4) (clk-seq-bool b)))\n"
            "(declare s (clk-seq-delay (range 2 $) (clk-seq-bool b)))\n"
            "(declare t (clk-seq-delay (range 2 2) (clk-seq-bool b)))\n",
            output.str());
}

// Documents and statements
TEST_F(EmitterTest, FullDocument) {
  BoolId a("a");
  BoolId b("b");
  BoolId c("c");
  ClkPropId p("p");

  printer.begin_list();
  printer.identifier("document");
  printer.lines();

  emit(printer, declare_input(a));
  emit(printer, declare_input(b));
  emit(printer, declare_input(c));
  emit(printer, declare(p, clk_prop_overlapped_implication(
      clk_seq_concat(clk_seq_bool(a), clk_seq_bool(b)),
      clk_prop_always(clk_prop_bool(c)))));
  emit(printer, assert_property(p));

  printer.end_list();

  EXPECT_EQ("(document\n"
            "  (declare-input a)\n"
            "  (declare-input b)\n"
            "  (declare-input c)\n"
            "  (declare p (clk-prop-overlapped-implication "
                "(clk-seq-concat (clk-seq-bool a) (clk-seq-bool b)) "
                "(clk-prop-always (clk-prop-bool c))))\n"
            "  (assert-property p)\n"
            ")",
            output.str());
}

} // namespace
} // namespace property_ir
