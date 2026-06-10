cmake_minimum_required(VERSION 3.16)
project(quantframe VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Release with debug info for profiling
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

add_compile_options(
    -Wall -Wextra -Wpedantic
    -O2
    $<$<CONFIG:Release>:-march=native>
)

include_directories(include)

set(ENGINE_SOURCES
    src/order_book.cpp
    src/strategy.cpp
    src/backtester.cpp
)

# Main CLI binary
add_executable(quantframe src/main.cpp ${ENGINE_SOURCES})
target_link_libraries(quantframe pthread)

# Test binary
add_executable(test_engine tests/test_engine.cpp ${ENGINE_SOURCES})
target_include_directories(test_engine PRIVATE tests)
target_link_libraries(test_engine pthread)

enable_testing()
add_test(NAME engine_tests COMMAND test_engine)
