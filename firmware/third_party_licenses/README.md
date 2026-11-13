# Binary runtime notices

The project C sources and original board support are Apache-2.0. Compiler toolchains are build-time dependencies and are not vendored. Generated binaries may include their standard runtime components; those components retain their licenses.

| Component | Use | Notice/source | Retrieved |
|---|---|---|---|
| Newlib | GNU Arm C runtime, including string/memory routines | `newlib-COPYING.NEWLIB.txt`, unmodified [upstream mirror](https://github.com/mirror/newlib-cygwin/blob/master/COPYING.NEWLIB) | 2026-11-13 |
| GCC runtime | Cortex-M soft-float arithmetic support | `gcc-COPYING.RUNTIME.txt`, unmodified [GCC14.3 runtime exception](https://github.com/gcc-mirror/gcc/blob/releases/gcc-14.3.0/COPYING.RUNTIME) | 2026-11-13 |
| Zig0.14.1 | Native Windows build compiler | `zig-LICENSE.txt`, copied unmodified from installed PyPI ziglang0.14.1 bundle | 2026-11-13 |
| mingw-w64 runtime | Windows native simulator C runtime | `mingw-w64-COPYING.txt`, copied unmodified from Zig0.14.1's bundled `lib/libc/mingw/COPYING` | 2026-11-13 |

No third-party motor drawings, firmware implementations, or vendor HAL source files are included. Public vendor specifications are cited in engineering documentation; they are not project measurements. These notices must accompany redistributed prebuilt binaries. Building natively on other operating systems uses the selected system C library and its corresponding license.
