cmake_minimum_required (VERSION 3.10)
project (RLSimDevice VERSION 0.1)

list(APPEND CMAKE_PREFIX_PATH)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -pthread -Wall")

find_package(Qt5 COMPONENTS Core Network REQUIRED)

add_executable(RLSimDevice
  src/main.cpp
  src/SimDevice.h
  src/SimDevice.cpp
)

target_link_libraries(RLSimDevice
  pthread
  Qt5::Core
  Qt5::Network
)
