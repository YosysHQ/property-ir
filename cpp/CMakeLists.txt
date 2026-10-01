cmake_minimum_required(VERSION 3.20)

project(property_ir LANGUAGES CXX)

add_library(property_ir STATIC
  src/sexpr.cpp
)

target_compile_features(property_ir PUBLIC cxx_std_17)

target_include_directories(property_ir PUBLIC
  "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

set_target_properties(property_ir PROPERTIES
  CXX_EXTENSIONS OFF
)
