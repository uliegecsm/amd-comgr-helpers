import logging
import os
import pathlib
import re
import subprocess
import typing

import typeguard

@typeguard.typechecked
def get_llvm_objdump_default() -> pathlib.Path:
    """
    Get the default path to `llvm-objdump`, using `ROCM_PATH` if available.
    """
    return pathlib.Path(os.environ.get('ROCM_PATH', default = '/opt/rocm')) / 'llvm' / 'bin' / 'llvm-objdump'

@typeguard.typechecked
def amdgcn(target : pathlib.Path, arch : str) -> typing.Callable[[pathlib.Path], bool]:
    """
    Create a matcher for `amdgcn-amd-amdhsa` files matching `target` and `arch`.
    """
    pattern = rf'{target.name}:[0-9].hipv[0-9]-amdgcn-amd-amdhsa--{arch}'

    @typeguard.typechecked
    def matching(path : pathlib.Path) -> bool:
        if not path.is_file():
            return False
        return re.match(
            pattern = pattern,
            string  = path.name,
        ) is not None

    return matching

@typeguard.typechecked
def extract_code_objects(*,
    binary : pathlib.Path,
    arch : str = 'gfx906',
    llvm_objdump : pathlib.Path = get_llvm_objdump_default(),
) -> typing.List[pathlib.Path]:
    """
    Extract code objects for `arch` from `binary` using `llvm_objdump`.
    """
    # As of ROCm 6.4.0, 'llvm-objdump' will effectively extract the code objects, but won't print their
    # path to the stdout. So we'll need to find them.
    cmd = [
        llvm_objdump,
        f'--arch-name={arch}',
        '--offloading',
        binary,
    ]
    logging.info(f"Extracting code objects from {binary} for {arch} with {cmd}.")
    subprocess.check_call(cmd)

    return list(filter(amdgcn(target = binary, arch = arch), binary.parent.iterdir()))
