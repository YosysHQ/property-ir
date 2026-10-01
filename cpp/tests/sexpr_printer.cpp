#include "property_ir/sexpr_printer.h"

#include <gtest/gtest.h>
#include <sstream>

namespace property_ir {
namespace {

class SExprPrinterTest : public testing::Test {
protected:
  std::ostringstream output;
  SExprPrinter printer{output};
};

TEST_F(SExprPrinterTest, NestedLists) {
  printer.list([&] {
    printer.identifier("outer");
    printer.identifier("a");
    printer.list([&] {
      printer.identifier("inner");
      printer.identifier("b");
    });
    printer.list([] {});
  });

  EXPECT_EQ("(outer a (inner b) ())", output.str());
}

TEST_F(SExprPrinterTest, MultilineDocument) {
  printer.list([&] {
    printer.identifier("document");
    printer.lines();
    printer.list([&] {
      printer.identifier("declare-input");
      printer.identifier("a");
    });
    printer.list([&] {
      printer.identifier("declare-input");
      printer.identifier("b");
    });
  });
  printer.line();

  EXPECT_EQ("(document\n"
            "  (declare-input a)\n"
            "  (declare-input b)\n"
            ")\n",
            output.str());
}

TEST_F(SExprPrinterTest, CompactSection) {
  printer.list([&] {
    printer.identifier("document");
    printer.lines();
    printer.list([&] {
      printer.compact();
      printer.identifier("declare");
      printer.identifier("p");
      printer.line();
      printer.list([&] {
        printer.identifier("constant");
        printer.line();
        printer.raw_atom("true");
      });
    });
  });

  EXPECT_EQ("(document\n"
            "  (declare p (constant true))\n"
            ")",
            output.str());
}

} // namespace
} // namespace property_ir
