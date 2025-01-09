import pathlib
import re
import subprocess

import typeguard

@typeguard.typechecked
def extract_code_objects(binary : pathlib.Path, arch : str = 'gfx906') -> list[pathlib.Path]:
    """
    Extract code objects for `arch` from `binary` using `roc-obj-ls` and `roc-obj-extract`.
    """
    roc_obj_ls = subprocess.check_output(['roc-obj-ls', '-v', binary]).decode()

    output_dir_cos = binary.with_suffix('.cos')
    output_dir_cos.mkdir(exist_ok = True)

    cos = []

    for line in roc_obj_ls.splitlines():
        if f'amdhsa--{arch}' in line:
            _, _, uri = line.split()
            match = re.match(pattern = rf'file://{binary}#offset=([0-9]+)&size=([0-9]+)', string = uri)
            subprocess.check_call(['roc-obj-extract', '-v', '-o', output_dir_cos, uri])
            cos.append(output_dir_cos / (binary.name + f'-offset{match.group(1)}-size{match.group(2)}.co'))

    return cos
