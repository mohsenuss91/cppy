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

from _cppy_test import *
import unittest

class TestStruct(unittest.TestCase):
    def setUp(self):
        self.a = a_struct()

    def test_default_access_method(self):
        self.assertEqual(self.a.f(), 'a_struct::f')

    def test_protected_method(self):
        self.assertEqual(self.a.g(), 'a_struct::g')

    def test_protected_virtual_method(self):
        self.assertEqual(self.a.h(), 'a_struct::h')

    def test_private_method(self):
        self.assertRaises(AttributeError, getattr, self.a, 'i')

class TestClass(unittest.TestCase):
    def setUp(self):
        self.a = a_class()

    def test_default_access_method(self):
        self.assertRaises(AttributeError, getattr, self.a, 'f')

    def test_protected_method(self):
        self.assertEqual(self.a.g(), 'a_class::g')

    def test_protected_virtual_method(self):
        self.assertEqual(self.a.h(), 'a_class::h')

    def test_public_method(self):
        self.assertEqual(self.a.i(), 'a_class::i')

class TestAbstractClass(unittest.TestCase):
    def test_construction(self):
        self.assertRaises(RuntimeError, an_abstract_class)

class TestPublicDerived(unittest.TestCase):
    def setUp(self):
        self.a = public_derived()

    def test_public_base_method(self):
        self.assertEqual(self.a.f(), 'an_abstract_class::f')

    def test_overridden_method(self):
        self.assertEqual(self.a.g(), 'public_derived::g')

if __name__ == "__main__":
    unittest.main()