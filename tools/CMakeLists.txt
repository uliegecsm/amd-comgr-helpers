add_executable(amd-comgr-helpers-parse-code-metadata)

target_sources(
    amd-comgr-helpers-parse-code-metadata
    PRIVATE
        parse_code_metadata.cpp
)

target_include_directories(
    amd-comgr-helpers-parse-code-metadata
    PRIVATE
        ${CMAKE_SOURCE_DIR}
)

target_link_libraries(
    amd-comgr-helpers-parse-code-metadata
    PRIVATE
        amd_comgr
)

install(
    TARGETS amd-comgr-helpers-parse-code-metadata
    RUNTIME
    DESTINATION bin
)

install(
    FILES ${CMAKE_CURRENT_SOURCE_DIR}/parse_code_metadata.py
    DESTINATION python/amd_comgr_helpers/tools/
)
