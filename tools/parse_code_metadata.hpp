#ifndef AMD_COMGR_HELPERS_TOOLS_PARSE_CODE_METADATA_HPP
#define AMD_COMGR_HELPERS_TOOLS_PARSE_CODE_METADATA_HPP

#include <iosfwd>
#include <map>
#include <string>
#include <variant>
#include <vector>

#include "amd_comgr/amd_comgr.h"

namespace amd::comgr::helpers
{

//! Meta data is a kind of JSON-serializable dictionary.
struct MetaData
{
    std::variant<
        std::map<std::string, MetaData>,
        std::vector<MetaData>,
        std::string
    > value;
};

//! Parse code object metadata using @c AMD Code Object Manager.
MetaData parse_code_metadata(const char* code, const size_t code_size, const amd_comgr_data_kind_t kind);

//! Streaming operator for @ref MetaData.
std::ostream& operator<<(std::ostream& out, const MetaData& metadata);

} // namespace amd::comgr::helpers

#endif // AMD_COMGR_HELPERS_TOOLS_PARSE_CODE_METADATA_HPP
