cppy
====

Generate Boost.Python code from C++ headers

Depends on libclang and the Python bindings.

To run the tests:

mkdir -p build && cd build  
cmake -DCMAKE_INSTALL_PREFIX=${prefix} ../  
make && make install  
python ${prefix}/cppy_test.py
