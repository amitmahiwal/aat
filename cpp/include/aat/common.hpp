#pragma once

#include <exception>
#include <string>
#include <pybind11/pybind11.h>
namespace py = pybind11;

#define ENUM_TO_STRING(type)                                                                                           \
  inline std::string type##_to_string(type typ) { return type##_names[static_cast<int>(typ)]; }
#define ENUM_FROM_STRING(type)                                                                                         \
  type inline type##_from_string(char* s) {                                                                            \
    if (_##type##_mapping.find(s) == _##type##_mapping.end()) {                                                        \
      throw py::value_error(s);                                                                                        \
    }                                                                                                                  \
    return _##type##_mapping[s];                                                                                       \
  }

class AATCPPException : public std::exception {
private:
  std::string msg = "";

public:
  AATCPPException(std::string msg)
    : msg(msg) {}

  const char*
  what() const noexcept override {
    return msg.c_str();
  }
};
