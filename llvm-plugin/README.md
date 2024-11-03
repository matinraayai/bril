# Compiler plugin For HW5 EECE 7398, Fall 2024

This project contains an LLVM compiler plugin that performs the following step at the very
last step of the optimization pipeline:

1. Clone the module being worked on.
2. Finds all outlined functions and global variables annotated with the keyword `path_point` and removes
   their definitions.
3. Embeds the cloned bitcode into a section of the final emitted ELF.

Embedding the LLVM IR bitcode of the ELF allows for easier generation of patched and instrumented binaries
at runtime because it retains important information like the calling convention of the functions to 
be patched.

## Build Instructions
1. First build the compiler plugin:
   ```shell
   mkdir build/ && cd build/
   cmake -G Ninja -DCMAKE_PREFIX_PATH=${PATH_TO_CLANG_COMPILER_INSTALLATION} .. 
   ninja
   ```
2. Build the example and inspect the modified LLVM IR before it gets embedded into the ELF:
   ```shell
   cd example/ && mkdir build/ && cd build/
   cmake -G Ninja -DCMAKE_CXX_COMPILER=${PATH_TO_CLANG_BIN} -DPASS_PATH=../../EECE7398CompilerPlugin.so ../
   ninja
   ```
