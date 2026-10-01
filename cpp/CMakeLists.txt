cmake_minimum_required(VERSION 3.20)

project(property_ir LANGUAGES CXX)

set(PROPERTY_IR_STANDALONE_PROJECT OFF)
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
  set(PROPERTY_IR_STANDALONE_PROJECT ON)
endif()

option(PROPERTY_IR_BUILD_TESTS "Build tests" ${PROPERTY_IR_STANDALONE_PROJECT})

add_library(property_ir STATIC
  src/sexpr_printer.cpp
)

target_compile_features(property_ir PUBLIC cxx_std_17)

target_include_directories(property_ir PUBLIC
  "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

set_target_properties(property_ir PROPERTIES
  CXX_EXTENSIONS OFF
)

if(PROPERTY_IR_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
