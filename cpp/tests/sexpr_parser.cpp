#include "property_ir/sexpr_parser.h"

#include <gtest/gtest.h>

namespace property_ir {
namespace {

TEST(SExprParserTest, NestedLists) {
  SExprParser parser(" (and a\n (not b)) ");
  using Kind = SExprToken::Kind;
  const SExprToken expected[] = {
      {Kind::BeginList, "(", 1}, {Kind::Atom, "and", 2},
      {Kind::Atom, "a", 6},      {Kind::BeginList, "(", 9},
      {Kind::Atom, "not", 10},   {Kind::Atom, "b", 14},
      {Kind::EndList, ")", 15},  {Kind::EndList, ")", 16},
      {Kind::End, "", 18},
  };

  for (const auto &want : expected) {
    const auto *token = std::get_if<SExprToken>(&parser.peek());
    ASSERT_NE(token, nullptr);
    EXPECT_EQ(want.kind, token->kind);
    EXPECT_EQ(want.text, token->text);
    EXPECT_EQ(want.offset, token->offset);

    auto result = parser.next();
    token = std::get_if<SExprToken>(&result);
    ASSERT_NE(token, nullptr);
    EXPECT_EQ(want.kind, token->kind);
    EXPECT_EQ(want.text, token->text);
    EXPECT_EQ(want.offset, token->offset);
  }
}

TEST(SExprParserTest, StickyError) {
  SExprParser parser(")");
  auto result = parser.next();
  const auto *error = std::get_if<SExprParseError>(&result);
  ASSERT_NE(error, nullptr);
  EXPECT_EQ(0u, error->offset);
  EXPECT_FALSE(error->message.empty());

  parser.advance();
  auto repeated = parser.next();
  const auto *repeated_error = std::get_if<SExprParseError>(&repeated);
  ASSERT_NE(repeated_error, nullptr);
  EXPECT_EQ(error->offset, repeated_error->offset);
  EXPECT_EQ(error->message, repeated_error->message);
}

} // namespace
} // namespace property_ir
