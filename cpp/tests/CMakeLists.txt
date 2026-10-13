find_package(GTest REQUIRED)
include(GoogleTest)

add_executable(sexpr_printer_test
  sexpr_printer.cpp
)

target_link_libraries(sexpr_printer_test PRIVATE
  property_ir
  GTest::gtest_main
)

set_target_properties(sexpr_printer_test PROPERTIES
  CXX_EXTENSIONS OFF
)

gtest_discover_tests(sexpr_printer_test)

add_executable(sexpr_parser_test
  sexpr_parser.cpp
)

target_link_libraries(sexpr_parser_test PRIVATE
  property_ir
  GTest::gtest_main
)

set_target_properties(sexpr_parser_test PROPERTIES
  CXX_EXTENSIONS OFF
)

gtest_discover_tests(sexpr_parser_test)

add_executable(emitter_test
  emitter.cpp
)

target_link_libraries(emitter_test PRIVATE
  property_ir
  GTest::gtest_main
)

set_target_properties(emitter_test PROPERTIES
  CXX_EXTENSIONS OFF
)

gtest_discover_tests(emitter_test)
