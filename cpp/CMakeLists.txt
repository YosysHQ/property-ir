cmake_minimum_required(VERSION 3.20)

project(property_ir LANGUAGES CXX)

set(PROPERTY_IR_STANDALONE_PROJECT OFF)
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
  set(PROPERTY_IR_STANDALONE_PROJECT ON)
endif()

if(PROPERTY_IR_STANDALONE_PROJECT)
  if(MSVC)
    add_compile_options(/GR-)
  else()
    add_compile_options(-fno-rtti)
  endif()
endif()

option(PROPERTY_IR_BUILD_TESTS "Build tests" ${PROPERTY_IR_STANDALONE_PROJECT})

find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)

set(PROPERTY_IR_SCHEMA "" CACHE FILEPATH
  "Pre-generated schema JSON; leave empty to export it using uv")
set(PROPERTY_IR_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
set(PROPERTY_IR_EMITTER_HEADER
  "${PROPERTY_IR_GENERATED_DIR}/property_ir/emitter_declarations.inc")
set(PROPERTY_IR_EMITTER_SOURCE
  "${PROPERTY_IR_GENERATED_DIR}/property_ir/emitter_definitions.inc")
set(PROPERTY_IR_EMITTER_GENERATOR
  "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate_emitter.py")

if(PROPERTY_IR_SCHEMA)
  get_filename_component(PROPERTY_IR_SCHEMA "${PROPERTY_IR_SCHEMA}" ABSOLUTE)
  if(NOT EXISTS "${PROPERTY_IR_SCHEMA}" OR IS_DIRECTORY "${PROPERTY_IR_SCHEMA}")
    message(FATAL_ERROR "Schema file not found: ${PROPERTY_IR_SCHEMA}")
  endif()
else()
  find_program(PROPERTY_IR_UV_EXECUTABLE NAMES uv REQUIRED)

  set(PROPERTY_IR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/..")
  set(PROPERTY_IR_PYTHON_DIR "${PROPERTY_IR_ROOT}/prototype/src")
  set(PROPERTY_IR_SCHEMA "${PROPERTY_IR_GENERATED_DIR}/schema.json")

  file(GLOB_RECURSE PROPERTY_IR_PYTHON_SOURCES CONFIGURE_DEPENDS
    "${PROPERTY_IR_PYTHON_DIR}/*.py")

  add_custom_command(
    OUTPUT "${PROPERTY_IR_SCHEMA}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${PROPERTY_IR_GENERATED_DIR}"
    COMMAND "${PROPERTY_IR_UV_EXECUTABLE}" run --project "${PROPERTY_IR_ROOT}" --locked
      python -B "${PROPERTY_IR_PYTHON_DIR}/schema_export.py" --output "${PROPERTY_IR_SCHEMA}"
    DEPENDS ${PROPERTY_IR_PYTHON_SOURCES}
      "${PROPERTY_IR_ROOT}/pyproject.toml" "${PROPERTY_IR_ROOT}/uv.lock"
    VERBATIM
  )
endif()

add_custom_command(
  OUTPUT "${PROPERTY_IR_EMITTER_HEADER}" "${PROPERTY_IR_EMITTER_SOURCE}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory
    "${PROPERTY_IR_GENERATED_DIR}/property_ir"
  COMMAND "${Python3_EXECUTABLE}" -B "${PROPERTY_IR_EMITTER_GENERATOR}"
    "${PROPERTY_IR_SCHEMA}" "${PROPERTY_IR_EMITTER_HEADER}" "${PROPERTY_IR_EMITTER_SOURCE}"
  DEPENDS "${PROPERTY_IR_SCHEMA}" "${PROPERTY_IR_EMITTER_GENERATOR}"
  VERBATIM
)

add_custom_target(property_ir_codegen
  DEPENDS "${PROPERTY_IR_EMITTER_HEADER}" "${PROPERTY_IR_EMITTER_SOURCE}")

add_library(property_ir STATIC
  src/emitter.cpp
  src/sexpr_parser.cpp
  src/sexpr_printer.cpp
)

add_dependencies(property_ir property_ir_codegen)

target_compile_features(property_ir PUBLIC cxx_std_17)

target_include_directories(property_ir PUBLIC
  "${CMAKE_CURRENT_SOURCE_DIR}/include"
  "${PROPERTY_IR_GENERATED_DIR}"
)

set_target_properties(property_ir PROPERTIES
  CXX_EXTENSIONS OFF
)

if(PROPERTY_IR_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()
