set(CLASSES a_struct a_class an_abstract_class public_derived protected_derived private_derived)
foreach(class ${CLASSES})
    string(TOLOWER ${class} class)
    list(APPEND GENERATED_SOURCES ${class}.cpp)
endforeach()

add_custom_command(OUTPUT ${GENERATED_SOURCES} COMMAND ${PYTHON_EXECUTABLE} ${PROJECT_SOURCE_DIR}/cppy.py
    --clang ${HAVE_LIBCLANG} -f ${CMAKE_CURRENT_SOURCE_DIR}/cppy_test.hpp --scope test ${CLASSES} VERBATIM)

set(MODULE ${CMAKE_CURRENT_BINARY_DIR}/module.cpp)
file(WRITE ${MODULE} "#include <boost/python.hpp>\n")
foreach(class ${CLASSES})
    file(APPEND ${MODULE} "void export_${class}();\n")
endforeach()
file(APPEND ${MODULE} "BOOST_PYTHON_MODULE(_cppy_test)\n{\n")
foreach(class ${CLASSES})
    file(APPEND ${MODULE} "    export_${class}();\n")
endforeach()
file(APPEND ${MODULE} "}")

add_library(_cppy_test MODULE ${MODULE} ${GENERATED_SOURCES})
set_property(TARGET _cppy_test PROPERTY PREFIX "")
set_property(TARGET _cppy_test APPEND PROPERTY INCLUDE_DIRECTORIES ${PYTHON_INCLUDE_DIRS} ${Boost_INCLUDE_DIRS})
target_link_libraries(_cppy_test ${Boost_PYTHON_LIBRARY} ${PYTHON_LIBRARIES})

set(CMAKE_INSTALL_PREFIX ${CMAKE_CURRENT_BINARY_DIR}/install CACHE PATH "" FORCE)
install(FILES cppy_test.py DESTINATION .)
install(TARGETS _cppy_test DESTINATION .)
