cmake_minimum_required(VERSION 3.14)
project(plagiarism_cpp_engine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(cpp_engine/include)

# C++ Core Executable CLI
add_executable(plagiarism_cli
    cpp_engine/src/huffman.cpp
    cpp_engine/src/winnowing.cpp
    cpp_engine/src/compressed_trie.cpp
    cpp_engine/src/binomial_heap.cpp
    cpp_engine/src/suffix_tree.cpp
    cpp_engine/src/kmp.cpp
    cpp_engine/src/dsu.cpp
    cpp_engine/main_cli.cpp
)

# Set binary target output path to build/bin/
set_target_properties(plagiarism_cli PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
