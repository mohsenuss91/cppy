cmake_minimum_required(VERSION 2.8)

project(cppy CXX)

if(${CMAKE_MODULE_LINKER_FLAGS})
    set(CMAKE_MODULE_LINKER_FLAGS ${CMAKE_MODULE_LINKER_FLAGS} "-Wl,-z,defs")
else()
    set(CMAKE_MODULE_LINKER_FLAGS "-Wl,-z,defs")
endif()

find_package(Boost COMPONENTS python REQUIRED)
find_package(PythonInterp REQUIRED)
find_package(PythonLibs REQUIRED)

find_library(HAVE_LIBCLANG clang PATH_SUFFIXES llvm-3.4/lib llvm-3.3/lib llvm-3.2/lib)
if(NOT HAVE_LIBCLANG)
    message(FATAL_ERROR "Unable to find libclang library")
endif()

add_subdirectory(test)
