cmake_minimum_required(VERSION 3.20 FATAL_ERROR)

project(amd-comgr-helpers LANGUAGES CXX)

include(cmake/modules/amd_comgr.cmake)

add_subdirectory(tools)

enable_testing()

add_subdirectory(tests)

include(CPack)
