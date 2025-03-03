import json
import os
import pathlib
import subprocess
import tempfile

from tools.parse_code_metadata import extract_code_objects

SOURCE_CODE = """
#include <iostream>

#include "hip/hip_runtime.h"

#define CHECK_HIP_CALL(__statement__)                    \\
    {                                                    \\
        const auto __status__ = __statement__;           \\
        if(__status__!= hipSuccess)                      \\
        {                                                \\
            std::cout << #__statement__ " status: "      \\
                << __status__                            \\
                << " " << hipGetErrorString(__status__)  \\
                << std::endl;                            \\
            throw std::runtime_error(                    \\
                std::string("Statement ") + #__statement__ " failed at " + __FILE__ + ":" + std::to_string(__LINE__)); \\
        }                                                \\
    }

__global__ void my_kernel(int* const data)
{
    const int idx = threadIdx.y;
    data[idx] = idx;
}

int main()
{
    //! Retrieve kernel attributes.
    hipFuncAttributes attrs{};
    CHECK_HIP_CALL(hipFuncGetAttributes(&attrs, (void*)my_kernel));
    std::cout << "> Kernel attributes:" << std::endl;
    std::cout << "\t- number of registers: " << attrs.numRegs << std::endl;

    //! Create a stream.
    hipStream_t stream = nullptr;
    CHECK_HIP_CALL(hipStreamCreate(&stream));

    //! Allocate data.
    constexpr size_t size = 128;
    int* data = nullptr;
    CHECK_HIP_CALL(hipMalloc((void**)&data, size * sizeof(int)));

    //! Launch kernel.
    constexpr dim3 grid  {1,    1, 1};
    constexpr dim3 block {1, size, 1};
    constexpr unsigned int shared = 0;

    my_kernel<<<grid, block, shared, stream>>>(data);

    //! Synchronize and cleanup.
    CHECK_HIP_CALL(hipStreamSynchronize(stream));
    CHECK_HIP_CALL(hipFree(data));
    CHECK_HIP_CALL(hipStreamDestroy(stream));
}
"""

EXPECTED_SGPR_COUNT = 10
EXPECTED_VGPR_COUNT = 2

def test_kernel_resource_usage_pass_analysis():
    """
    Ensure that the kernel resource usage pass analysis agrees with
    `EXPECTED_SGPR_COUNT` and `EXPECTED_VGPR_COUNT`.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = pathlib.Path(tmpdir_str)
        source = tmpdir / 'test.cpp'
        binary = tmpdir / 'test.exe'
        source.write_text(SOURCE_CODE)
        compilation = subprocess.check_output(
            args = [
                'hipcc', '--offload-arch=gfx906',
                '-Rpass-analysis=kernel-resource-usage',
                '-Wall', '-Wextra', '-Werror',
                source,
                '-o', binary,
            ],
            cwd = tmpdir,
            stderr = subprocess.STDOUT,
        ).decode()
        assert f"test.cpp:21:1: remark:     SGPRs: {EXPECTED_SGPR_COUNT} [-Rpass-analysis=kernel-resource-usage]" in compilation
        assert f"test.cpp:21:1: remark:     VGPRs: {EXPECTED_VGPR_COUNT} [-Rpass-analysis=kernel-resource-usage]" in compilation

def test_kernel_resource_usage_isa_save_temps():
    """
    Ensure that the kernel resource usage from ISA inspection (generated by `--save-temps`) agrees with
    `EXPECTED_SGPR_COUNT` and `EXPECTED_VGPR_COUNT`.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = pathlib.Path(tmpdir_str)
        source = tmpdir / 'test.cpp'
        binary = tmpdir / 'test.exe'
        source.write_text(SOURCE_CODE)
        subprocess.check_call(
            args = [
                'hipcc', '--offload-arch=gfx906',
                '--save-temps',
                '-Wall', '-Wextra', '-Werror',
                source,
                '-o', binary,
            ],
            cwd = tmpdir,
            stderr = subprocess.STDOUT,
        )
        assembly = (tmpdir / 'test-hip-amdgcn-amd-amdhsa-gfx906.s').read_text()
        assert f'.sgpr_count:     {EXPECTED_SGPR_COUNT}' in assembly
        assert f'.vgpr_count:     {EXPECTED_VGPR_COUNT}' in assembly

def test_kernel_resource_usage_from_code_object():
    """
    Extract kernel resource usage from code object using `AMD` *Code Object Manager*.
    """
    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = pathlib.Path(tmpdir_str)
        source = tmpdir / 'test.cpp'
        binary = tmpdir / 'test.exe'
        source.write_text(SOURCE_CODE)
        subprocess.check_call(
            args = [
                'hipcc', '--offload-arch=gfx906',
                '-Wall', '-Wextra', '-Werror',
                source,
                '-o', binary,
            ],
            cwd = tmpdir,
        )
        cos = extract_code_objects(binary = binary, arch = 'gfx906')
        assert len(cos) == 1

        metadata_json = tmpdir / 'test.metadata.json'
        subprocess.check_call(
            args = [
                os.environ['PARSER_BINARY'],
                cos[0],
                metadata_json,
            ],
            cwd = tmpdir,
        )

        with open(metadata_json, 'r') as f:
            metadata = json.load(f)

        assert len(metadata['amdhsa.kernels']) == 1
        assert metadata['amdhsa.kernels'][0]['.name']       == '_Z9my_kernelPi'
        assert metadata['amdhsa.kernels'][0]['.sgpr_count'] == str(EXPECTED_SGPR_COUNT)
        assert metadata['amdhsa.kernels'][0]['.vgpr_count'] == str(EXPECTED_VGPR_COUNT)
