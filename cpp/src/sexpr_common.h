#ifndef YOSYS_PROPERTY_IR_SEXPR_COMMON_H
#define YOSYS_PROPERTY_IR_SEXPR_COMMON_H

namespace property_ir {

inline bool is_atom_char(char c) {
  return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
         (c >= '0' && c <= '9') || c == '_' || c == '$' || c == ':' || c == '-';
}

} // namespace property_ir

#endif
