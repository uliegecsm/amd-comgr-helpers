cmake_minimum_required(VERSION 3.23 FATAL_ERROR)

#---- Read the version file.
file(READ version.json VERSION_JSON)

#---- Get the version of kokkos-utils.
string(JSON AMD_COMGR_HELPERS_VERSION GET "${VERSION_JSON}" "amd_comgr_helpers" "value")

project(
    amd-comgr-helpers
    VERSION ${AMD_COMGR_HELPERS_VERSION}
    LANGUAGES CXX
)

include(cmake/modules/amd_comgr.cmake)

add_subdirectory(tools)

enable_testing()

add_subdirectory(tests)

include(CPack)
