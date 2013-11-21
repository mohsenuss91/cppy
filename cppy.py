# Copyright (C) 2013  Vitaly Budovski
#
# This file is part of cppy.
#
# cppy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cppy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cppy.  If not, see <http://www.gnu.org/licenses/>.

from clang.cindex import *

class cxx_method(object):
    def __init__(self, name, return_type, scope = ''):
        self.name = name
        self.return_type = return_type
        self.parameters = list()
        self.default_parameters = 0
        self.scope = scope
        self.is_const = False
        self.is_volatile = False
        self.is_static = False
        self.is_virtual = False
        self.is_pure_virtual = False

    def prototype(self):
        value = 'static ' if self.is_static else ''
        value += self.return_type + ' ' + self.name + '('
        value += ', ' . join(type + ' ' + name + (' = ' + default if default is not None else '') for type, name,
            default in self.parameters)
        value += ')'
        if self.is_const:
            value += ' const'

        return value

    def function_pointer(self, number = None):
        value = self.return_type + ' (' + self.scope + '::*' + self.name
        if number:
            value += str(number)
        value += ')(' + ', ' . join(type for type, name, value in self.parameters) + ') = &' + self.scope
        value += '::' + self.name + ';'
        if self.is_const:
            value += ' const'

        return value

    def boost_python_definition(self, access, number = None):
        value = '.def("' + self.name + '", '
        if number:
            function = self.name + str(number)
        else:
            function = '&' + self.scope
            function_wrapper = function + '_wrapper'
            function += '::' + self.name
            function_wrapper += '::' + self.name
        if self.is_pure_virtual:
            value += 'pure_virtual(' + function_wrapper + ')'
        elif self.is_virtual:
            name = function_wrapper.find(self.name)
            if access == 'protected':
                function = function_wrapper
            value += function + ', ' + function_wrapper[0 : name] + 'default_' + function_wrapper[name : ]
        else:
            value += function_wrapper if function_wrapper else function
        if self.return_type[-1] == '&':
            value += ', '
            if self.default_parameters:
                value += self.name
                if number:
                    value += str(number)
                value += '_overloads()['
            value += 'return_value_policy<copy_'
            if not self.return_type.startswith('const '):
                value += 'non_'
            value += 'const_reference>()'
            if self.default_parameters:
                value += ']'
        elif self.return_type[-1] == '*':
            value += ', '
            if self.default_parameters:
                value += self.name
                if number:
                    value += str(number)
                value += '_overloads()['
            value += 'return_internal_reference<>()'
            if self.default_parameters:
                value += ']'
        value += ')'

        if self.is_static:
            value += '.staticmethod("' + self.name + '")'

        return value

    def boost_python_override(self):
        if self.is_pure_virtual:
            value = self.prototype() + ' { '
            if self.return_type != 'void':
                value += 'return '
            value += 'this->get_override("' + self.name + '")('
            value += ', ' . join(name for type, name, default in self.parameters) + '); }'
        elif self.is_virtual:
            value = self.prototype() + ' { '
            value += 'if(override f = this->get_override("' + self.name + '")) { '
            if self.return_type != 'void':
                value += 'return '
            value += 'f('
            params = ', ' . join(name for type, name, default in self.parameters)
            value += params + '); } '
            if self.return_type != 'void':
                value += 'return '
            value += self.scope + '::' + self.name + '(' + params + '); } '
            name = self.prototype().find(self.name)
            value += self.prototype()[0 : name] + 'default_' + self.prototype()[name : ] + ' { '
            if self.return_type != 'void':
                value += 'return '
            value += self.scope + '::' + self.name + '(' + params + '); } '

        else:
            value = '// ' + self.name

        return value

    def boost_python_overload(self, number = None):
        function = self.name
        if number:
            function += str(number)
        value = 'BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS(' + function + '_overloads, ' + self.scope
        if self.is_virtual:
            value += '_wrapper'
        value += '::'
        value += self.name
        value += ', ' + str(len(self.parameters) - self.default_parameters) + ', ' + str(len(self.parameters)) + ')'

        return value

class cxx_class(object):
    def __init__(self, name, is_struct, scope = ''):
        self.name = name
        self.is_struct = is_struct
        self.scope = scope
        self.methods = {'public' : {}, 'protected' : {}}
        self.is_abstract = False
        self.forward_declarations = list()
        self.bases = list()

    def insert(self, method, access = 'public'):
        if not self.is_abstract and method.is_pure_virtual:
            self.is_abstract = True

        if not method.name in self.methods[access]:
            self.methods[access][method.name] = list()

        self.methods[access][method.name].append(method)

    def process(self, cursor):
        access = 'public' if self.is_struct else 'private'
        for i in cursor.get_children():
            if i.kind == CursorKind.FUNCTION_DECL or i.kind == CursorKind.CXX_METHOD:
                if access in ['public', 'protected']:
                    self.insert(self.__process_method(i), access)
            elif i.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                access = i.get_tokens().next().spelling
            elif i.kind == CursorKind.CXX_BASE_SPECIFIER:
                token = i.get_tokens().next()
                if token.kind == TokenKind.KEYWORD:
                    if token.spelling == 'public':
                        self.bases.append(i.get_definition().spelling)
                elif self.is_struct:
                    self.bases.append(i.get_definition().spelling)

    def __process_method(self, cursor):
        m = cxx_method(cursor.spelling, self.__process_type(cursor.result_type))
        m.scope = self.name

        for p in cursor.get_children():
            if p.kind == CursorKind.PARM_DECL:
                m.parameters.append((self.__process_type(p.type), p.displayname))

        usr = cursor.get_usr()
        specifier = usr.rfind('#')
        if specifier not in [-1, len(usr) - 1] and not cursor.is_static_method():
            if ord(usr[specifier + 1]) & 0x1:
                m.is_const = True
            if ord(usr[specifier + 1]) & 0x4:
                m.is_volatile = True

        end_of_declaration = False
        set_default_value = False
        default_value = ''
        parameter = 0
        for token in cursor.get_tokens():
            if token.kind == TokenKind.KEYWORD and token.spelling == 'virtual':
                m.is_virtual = True
            elif token.kind == TokenKind.PUNCTUATION and token.spelling == ')':
                end_of_declaration = True
                if set_default_value:
                    m.parameters[parameter] += (default_value,)
                    m.default_parameters += 1
                elif len(m.parameters):
                    m.parameters[parameter] += (None,)
                default_value = ''
                set_default_value = False
            elif token.kind == TokenKind.PUNCTUATION and token.spelling == ',':
                if set_default_value:
                    m.parameters[parameter] += (default_value,)
                    m.default_parameters += 1
                else:
                    m.parameters[parameter] += (None,)

                default_value = ''
                set_default_value = False
                parameter += 1
            elif token.kind == TokenKind.PUNCTUATION and token.spelling == ';':
                break
            elif token.kind == TokenKind.PUNCTUATION and token.spelling == '{':
                break
            elif token.kind == TokenKind.PUNCTUATION and token.spelling == '=':
                if end_of_declaration:
                    m.is_pure_virtual = True
                    break
                set_default_value = True
            elif token.kind != TokenKind.COMMENT:
                if set_default_value:
                    default_value += token.spelling

        if cursor.is_static_method():
            m.is_static = True

        m.return_type = self.__process_type(cursor.result_type)

        return m

    def __process_type(self, type):
        name = ''

        if type.kind == TypeKind.POINTER:
            if type.get_pointee().is_const_qualified():
                name += 'const '
            name += self.__process_type(type.get_pointee()) + ' *'
        elif type.kind == TypeKind.LVALUEREFERENCE:
            if type.get_pointee().is_const_qualified():
                name += 'const '
            name += self.__process_type(type.get_pointee()) + ' &'
        elif type.kind == TypeKind.TYPEDEF:
            name += type.get_declaration().spelling
        elif type.kind == TypeKind.ENUM:
            name += type.get_declaration().spelling
        elif type.kind == TypeKind.VOID:
            name += 'void'
        elif type.kind == TypeKind.BOOL:
            name += 'bool'
        elif type.kind == TypeKind.USHORT:
            name += 'unsigned short'
        elif type.kind == TypeKind.SHORT:
            name += 'short'
        elif type.kind == TypeKind.UINT:
            name += 'unsigned int'
        elif type.kind == TypeKind.INT:
            name += 'int'
        elif type.kind == TypeKind.FLOAT:
            name += 'float'
        elif type.kind == TypeKind.DOUBLE:
            name += 'double'
        elif type.kind == TypeKind.ULONG:
            name += 'unsigned long'
        elif type.kind == TypeKind.LONG:
            name += 'long'
        elif type.kind == TypeKind.UCHAR:
            name += 'unsigned char'
        elif type.kind == TypeKind.CHAR_S:
            name += 'char'
        elif type.kind == TypeKind.RECORD:
            if not type.get_declaration().is_definition():
                self.forward_declarations.append(type.get_declaration().get_usr())

            name += type.get_declaration().spelling
        elif type.kind == TypeKind.UNEXPOSED:
            # Output the name and hope for the best.
            # If parent is a class or struct, this is probably an inner class/struct that needs to be qualified.
            parent = type.get_declaration().lexical_parent
            if parent.kind == CursorKind.CLASS_DECL or parent.kind == CursorKind.STRUCT_DECL:
                name += parent.spelling + '::'

            name += type.get_declaration().spelling
        else:
            name += 'UNHANDLED:' + type.kind.spelling 

        return name

    def boost_python_class(self, includes = list()):
        f = open(self.name.lower() + '.cpp', 'w')
        f.write('#include <boost/python.hpp>\n')
        for i in includes:
            f.write('#include <' + i + '>\n')
        f.write('using namespace boost::python;\n')
        if self.scope:
            f.write('using namespace ' + self.scope + ';\n')
        f.write('\n')

        function_pointers = list()
        boost_python_definitions = list()
        boost_python_overrides = list()
        boost_python_overloads = list()

        for access in self.methods.keys():
            for method, declarations in self.methods[access].items():
                if len(declarations) > 1:
                    for i in range(0, len(declarations)):
                        if declarations[i].default_parameters and not declarations[i].is_pure_virtual:
                            boost_python_overloads.append(declarations[i].boost_python_overload(i + 1))

                        function_pointers.append(declarations[i].function_pointer(i + 1))

                        if declarations[i].is_virtual:
                            boost_python_definitions.append(declarations[i].boost_python_definition(access, i + 1))
                            boost_python_overrides.append(declarations[i].boost_python_override())
                        else:
                            if access == 'protected':
                                boost_python_overrides.append('using ' + declarations[i].scope + '::' +
                                    declarations[i].name + ';')
                            boost_python_definitions.append(declarations[i].boost_python_definition(access, i + 1))

                else:
                    if declarations[0].default_parameters and not declarations[0].is_pure_virtual:
                        boost_python_overloads.append(declarations[0].boost_python_overload())

                    if declarations[0].is_virtual:
                        boost_python_definitions.append(declarations[0].boost_python_definition(access))
                        boost_python_overrides.append(declarations[0].boost_python_override())
                    else:
                        if access == 'protected':
                            boost_python_overrides.append('using ' + declarations[0].scope + '::' +
                                declarations[0].name + ';')
                        boost_python_definitions.append(declarations[0].boost_python_definition(access))

        for p in function_pointers:
            f.write(p + '\n')
        if len(function_pointers):
            f.write('\n')

        if self.is_abstract and len(boost_python_overloads):
            f.write('struct ' + self.name + '_wrapper;\n')
        for o in boost_python_overloads:
            f.write(o + '\n')
        if len(boost_python_overloads):
            f.write('\n')

        f.write('struct ' + self.name + '_wrapper: public ' + self.name + ', public wrapper<' + self.name +
            '>\n{\n')
        for o in boost_python_overrides:
            f.write('    ' + o + '\n')
        f.write('};\n\n')

        f.write('void export_' + self.name + '()\n{\n')

        f.write('    class_<' + self.name + '_wrapper, ')
        if len(self.bases):
            f.write('bases<' + ', ' . join(base for base in self.bases) + '>, ')
        f.write('boost::noncopyable>("' + self.name + '"')
        if self.is_abstract:
            f.write(', no_init')
        f.write(')\n')
        for v in boost_python_definitions:
            f.write('        ' + v + '\n')
        f.write('    ;\n}')

        f.close()


def process_class(cursor, scope):
    index = Index.create()
    tu = index.parse(cursor.get_definition().location.file.name, args = include_paths + ['-xc++'])

    location = SourceLocation.from_position(tu, cursor.location.file, cursor.location.line, cursor.location.column)
    cursor2 = Cursor.from_location(tu, location)

    c = cxx_class(cursor2.spelling, cursor2.kind == CursorKind.STRUCT_DECL, scope)
    c.process(cursor2)

    return c

exported_classes = dict()
def process_namespace(cursor, classes):

    for i in cursor.get_children():
        if i.kind == CursorKind.NAMESPACE:
            process_namespace(i, classes)
        if i.kind == CursorKind.CLASS_DECL or i.kind == CursorKind.STRUCT_DECL:
            if i.is_definition():
                c = None
                if i.spelling in classes:
                    c = process_class(i, cursor.spelling)
                exported_classes[i.get_usr()] = c, i.location.file.name

def process_scope(cursor, scope, classes):
    try:
        si = scope.next()

        for i in cursor.get_children():
            if i.spelling == si:
                process_scope(i, scope, classes)
    except:
        for i in cursor.get_children():
            if i.spelling == si:
                if i.kind == CursorKind.NAMESPACE:
                    process_namespace(i, classes)


def main():
    import argparse
    import sys

    options = argparse.ArgumentParser(description = 'Generate Boost.Python definitions')
    options.add_argument('--clang', help = 'path to libclang')
    options.add_argument('--scope', help = 'scope to search in (global if unspecified)')
    options.add_argument('classes', metavar = ('CLASS'), nargs = '+', help =
        'a class/struct to generate definition from')
    options.add_argument('-I', metavar = ('DIRECTORY'), action = 'append', help =
        'add directory to include search path')
    options.add_argument('-f', '--filename', required = True, help = 'filename to process')

    args = options.parse_args()

    if args.clang:
        Config.set_library_file(args.clang)

    global include_paths
    if args.I:
        include_paths = ['-I' + i for i in args.I]
    else:
        include_paths = list()

    scope = iter([])
    if args.scope:
        scope = iter(args.scope.split('::'))

    index = Index.create()
    tu = index.parse(args.filename, args = include_paths + ['-xc++'])

    if len(tu.diagnostics):
        for diag in tu.diagnostics:
            print diag
        sys.exit(1)

    process_scope(tu.cursor, scope, args.classes)

    for usr, (c, location) in exported_classes.iteritems():
        if c:
            print 'Writing Boost.Python definition for class ' + c.name
            includes = [location]
            for d in set(c.forward_declarations):
                if d in exported_classes:
                    includes.append(exported_classes[d][1])
                else:
                    print 'Warning: no definition for ' + d + ' found in this translation unit'
            c.boost_python_class(includes)


if __name__ == '__main__':
    main()
