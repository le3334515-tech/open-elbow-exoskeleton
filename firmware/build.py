"""Build native C simulator/tests or actual STM32F407 ELF/BIN.
SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

FW = Path(__file__).resolve().parent
ROOT = FW.parent


def run(args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True)


def find_zig():
    found = shutil.which("zig")
    if found:
        return found
    try:
        import ziglang
        candidate = Path(ziglang.__file__).parent / ("zig.exe" if os.name == "nt" else "zig")
        if candidate.exists():
            return str(candidate)
    except ImportError:
        pass
    # Workspace-local provisioning path, outside the source repository.
    for ancestor in ROOT.parents:
        candidate = ancestor / "work/toolchains/zig-python/ziglang/zig.exe"
        if candidate.exists():
            return str(candidate)
    return None


def build_host(compiler=None):
    out = FW / "build"
    out.mkdir(exist_ok=True)
    if compiler:
        cc = [compiler]
    elif shutil.which("cc"):
        cc = ["cc"]
    elif shutil.which("gcc"):
        cc = ["gcc"]
    elif zig := find_zig():
        cc = [zig, "cc"]
    else:
        raise SystemExit("No native C compiler. Install GCC/Clang, or: python -m pip install ziglang==0.14.1")
    flags = ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Wno-misleading-indentation", "-I", FW / "include"]
    core = [FW / "src/control.c", FW / "src/protocol.c"]
    ext = ".exe" if os.name == "nt" else ""
    for name, source in [("host_sim", "src/host_sim.c"), ("control_tests", "tests/control_tests.c")]:
        run(cc + flags + core + [FW / source, "-o", out / (name + ext)] + ([] if os.name == "nt" else ["-lm"]))
    run([out / ("control_tests" + ext)])


def build_arm(compiler=None):
    out = FW / "build/stm32"
    out.mkdir(parents=True, exist_ok=True)
    gcc = compiler or shutil.which("arm-none-eabi-gcc")
    if not gcc:
        raise SystemExit("Install official GNU Arm Embedded toolchain and add arm-none-eabi-gcc to PATH, or pass --compiler path.")
    sources = [FW / p for p in ["src/control.c", "src/protocol.c", "board/stm32f407.c", "board/startup.c"]]
    flags = ["-mcpu=cortex-m4", "-mthumb", "-mfloat-abi=soft", "-std=c11", "-Os", "-ffreestanding", "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror", "-Wno-misleading-indentation", "-I", FW / "include"]
    elf = out / "open_elbow.elf"
    run([gcc] + flags + sources + ["-T", FW / "board/stm32f407.ld", "-nostartfiles", "--specs=nosys.specs", "-Wl,--gc-sections", "-Wl,-Map=" + str(out / "open_elbow.map"), "-o", elf])
    objcopy = str(Path(gcc).with_name("arm-none-eabi-objcopy" + (".exe" if os.name == "nt" else ""))) if Path(gcc).parent != Path(".") else "arm-none-eabi-objcopy"
    run([objcopy, "-O", "binary", elf, out / "open_elbow.bin"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["host", "stm32", "all"], default="host")
    parser.add_argument("--compiler")
    args = parser.parse_args()
    run([sys.executable, ROOT / "tools/generate_config.py"])
    if args.target in ("host", "all"):
        build_host(args.compiler if args.target == "host" else None)
    if args.target in ("stm32", "all"):
        build_arm(args.compiler)
