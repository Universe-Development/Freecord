# Set the minimum required version of CMake
cmake_minimum_required(VERSION 3.16)

# Set the project name and C++ standard
project(Freecord)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Fetch Dependencies ---
# We will use FetchContent to download and configure GLFW automatically.
include(FetchContent)

FetchContent_Declare(
  glfw
  GIT_REPOSITORY https://github.com/glfw/glfw.git
  GIT_TAG        3.3.8
)
FetchContent_MakeAvailable(glfw)

# Find OpenGL - it's usually available on the system
find_package(OpenGL REQUIRED)

# --- Source Files ---
# List all the source files for your application and for ImGui
set(IMGUI_SOURCES
    imgui/imgui.cpp
    imgui/imgui_demo.cpp
    imgui/imgui_draw.cpp
    imgui/imgui_tables.cpp
    imgui/imgui_widgets.cpp
)

# You will need the backend files from the official ImGui repository.
# Place them in a 'backends' folder next to your 'imgui' folder.
set(IMGUI_BACKEND_SOURCES
    imgui/backends/imgui_impl_glfw.cpp
    imgui/backends/imgui_impl_opengl3.cpp
)

# Create the executable for your application
add_executable(Freecord
    main.cpp
    ${IMGUI_SOURCES}
    ${IMGUI_BACKEND_SOURCES}
)

# --- Include Directories ---
# Tell the compiler where to find header files
target_include_directories(Freecord PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/imgui
    ${CMAKE_CURRENT_SOURCE_DIR}/backends
)

# --- Link Libraries ---
# Link your application against the necessary libraries
target_link_libraries(Freecord PUBLIC
    glfw
    OpenGL::GL
)

# --- Platform Specific Settings ---
# Add necessary definitions for Windows
if(WIN32)
    target_compile_definitions(Freecord PRIVATE "IMGUI_IMPL_OPENGL_LOADER_GLAD")
endif()
