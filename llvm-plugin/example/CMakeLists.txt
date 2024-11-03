cmake_minimum_required(VERSION 3.21)

project(compiler-plugin-example
        VERSION 0.0.1
        LANGUAGES C CXX
        DESCRIPTION "Example for applying the compiler plugin for Homework 5 of EECE7398, Fall 2024"
)

set(CMAKE_CXX_STANDARD 20)


add_executable(ExampleExecutable Example.cpp)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fpass-plugin=${PASS_PATH}")