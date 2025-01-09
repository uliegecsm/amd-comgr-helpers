#include <filesystem>
#include <fstream>
#include <iostream>

#include "tools/parse_code_metadata.hpp"

#define CHECK_AMD_COMGR(__statement__)                      \
    {                                                       \
        const auto status = __statement__;                  \
        if(status != AMD_COMGR_STATUS_SUCCESS)              \
        {                                                   \
            std::string msg = std::string("Statement:\n\t") \
                + #__statement__                            \
                + "\nfailed with error code "               \
                + std::to_string(status);                   \
            throw std::runtime_error(std::move(msg));       \
        }                                                   \
    }

namespace amd::comgr::helpers
{

//! Retrieve the metadata string.
std::string get_metadata_string(const amd_comgr_metadata_node_t& metadata)
{
    size_t size = 0;
    CHECK_AMD_COMGR(amd_comgr_get_metadata_string(metadata, &size, nullptr));

    std::string str(size - 1, ' ');
    CHECK_AMD_COMGR(amd_comgr_get_metadata_string(metadata, &size, str.data()));

    return str;
}

std::ostream& operator<<(std::ostream& out, const std::map<std::string, MetaData>& map)
{
    if(!map.empty())
    {
        out << '{';
        size_t ipair = 0;
        for(const auto& e : map)
        {
            out << '"' << e.first << "\":" << e.second;
            if(++ipair < map.size()) out << ',';
        }
        out << '}';
    }
    return out;
}

std::ostream& operator<<(std::ostream& out, const std::vector<MetaData>& list)
{
    if(!list.empty())
    {
        out << '[';
        size_t ielem = 0;
        for(const auto& e : list)
        {
            out << e;
            if(++ielem < list.size()) out << ',';
        }
        out << ']';
    }
    return out;
}

std::ostream& operator<<(std::ostream& out, const MetaData& metadata)
{
    if(std::holds_alternative<std::string>(metadata.value))
        out << '"' << std::get<std::string>(metadata.value) << '"';
    else
        std::visit([&out](const auto& arg) { out << arg; }, metadata.value);
    return out;
}

MetaData parse_metadata(const amd_comgr_metadata_node_t& metadata)
{
    amd_comgr_metadata_kind_t kind;
    CHECK_AMD_COMGR(amd_comgr_get_metadata_kind(metadata, &kind));

    switch(kind)
    {
        case AMD_COMGR_METADATA_KIND_MAP:
        {
            std::map<std::string, MetaData> result {};

            //! Retrieve map keys.
            CHECK_AMD_COMGR(amd_comgr_iterate_map_metadata(
                metadata,
                [](amd_comgr_metadata_node_t key, amd_comgr_metadata_node_t, void* userdata) -> amd_comgr_status_t
                {
                    static_cast<std::map<std::string, MetaData>*>(userdata)->operator[](get_metadata_string(key)) = MetaData{};
                    return AMD_COMGR_STATUS_SUCCESS;
                },
                (void*)&result
            ));

            //! Retrieve map values.
            for(auto& pair : result)
            {
                amd_comgr_metadata_node_t value;
                CHECK_AMD_COMGR(amd_comgr_metadata_lookup(metadata, pair.first.c_str(), &value));

                pair.second = parse_metadata(value);

                CHECK_AMD_COMGR(amd_comgr_destroy_metadata(value));
            }
            return MetaData{.value = std::move(result)};
        }
        case AMD_COMGR_METADATA_KIND_LIST:
        {
            std::vector<MetaData> result {};

            //! Retrieve list size.
            size_t size = 0;
            CHECK_AMD_COMGR(amd_comgr_get_metadata_list_size(metadata, &size));

            //! Retrieve list values.
            for(size_t ielem = 0; ielem < size; ++ielem)
            {
                amd_comgr_metadata_node_t value;
                CHECK_AMD_COMGR(amd_comgr_index_list_metadata(metadata, ielem, &value));

                result.push_back(parse_metadata(value));

                CHECK_AMD_COMGR(amd_comgr_destroy_metadata(value));
            }
            return MetaData{.value = std::move(result)};
        }
        case AMD_COMGR_METADATA_KIND_STRING:
            return MetaData{.value = get_metadata_string(metadata)};
        default:
            throw std::runtime_error("Unsupported metadata kind.");
    }
}

MetaData parse_code_metadata(const char* code, const size_t code_size, const amd_comgr_data_kind_t kind)
{
    amd_comgr_data_t data {0};
    CHECK_AMD_COMGR(amd_comgr_create_data(kind, &data));
    CHECK_AMD_COMGR(amd_comgr_set_data(data, code_size, code));

    amd_comgr_metadata_node_t metadata {0};
    CHECK_AMD_COMGR(amd_comgr_get_data_metadata(data, &metadata));

    auto result = parse_metadata(metadata);

    CHECK_AMD_COMGR(amd_comgr_destroy_metadata(metadata));

    CHECK_AMD_COMGR(amd_comgr_release_data(data));

    return result;
}

} // namespace amd::comgr::helpers

int main(int argc, char* argv[])
{
    if(argc != 3)
        throw std::runtime_error("Wrong usage.");

    const std::filesystem::path code_object(argv[1]);
    const std::filesystem::path output     (argv[2]);

    std::cout << "> Reading code object from " << code_object << '.' << std::endl;

    std::ifstream input(code_object, std::ios::in | std::ios::binary);

    if(!input.is_open()) throw std::runtime_error(code_object);

    std::vector<char> buffer(std::filesystem::file_size(code_object));

    if(buffer.size() == 0) throw std::runtime_error("Unexpected zero size file.");

    input.seekg(0, std::ios::beg);
    input.read(buffer.data(), buffer.size());
    input.close();

    std::cout << "> Read " << buffer.size() << " bytes from " << code_object << '.' << std::endl;

    const auto result = amd::comgr::helpers::parse_code_metadata(buffer.data(), buffer.size(), AMD_COMGR_DATA_KIND_EXECUTABLE);

    std::cout << "> Writing metadata to " << output << '.' << std::endl;

    std::ofstream output_stream(output);

    if(!output_stream.is_open()) throw std::runtime_error(output);

    output_stream << result;

    return EXIT_SUCCESS;
}
