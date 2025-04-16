add_test(
    NAME tests_tools_parse_code_metadata
    COMMAND python3 -m pytest ${CMAKE_CURRENT_SOURCE_DIR}/test_parse_code_metadata.py -s --log-cli-level=info
)
set_property(
    TEST tests_tools_parse_code_metadata
    APPEND
    PROPERTY
        ENVIRONMENT "PYTHONPATH=${CMAKE_SOURCE_DIR}"
)
set_property(
    TEST tests_tools_parse_code_metadata
    APPEND
    PROPERTY
        ENVIRONMENT "PARSER_BINARY=$<TARGET_FILE:amd-comgr-helpers-parse-code-metadata>"
)
