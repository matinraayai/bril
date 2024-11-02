cmake_minimum_required(VERSION 3.21)

project(llvm-embed-modified-bitcode
        VERSION 0.0.1
        LANGUAGES C CXX
        DESCRIPTION "Compiler plugin for Homework 5 of EECE7398, Fall 2024"
)

set(CMAKE_CXX_STANDARD 20)

find_package(LLVM REQUIRED CONFIG)

if (${LLVM_EECE_7398_COMPILER_PLUGIN})
    message(WARNING "Setting LLVM_EECE_7398_COMPILER_PLUGIN=ON is not supported")
endif ()

include(AddLLVM)
add_llvm_pass_plugin(EECE7398CompilerPlugin
        EmbedModifiedBitcodePass.hpp
        EmbedModifiedBitcodePass.cpp)
target_include_directories(EECE7398CompilerPlugin PUBLIC ${LLVM_INCLUDE_DIRS})