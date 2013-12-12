/*
* Copyright (C) 2013  Vitaly Budovski
*
* This file is part of cppy.
*
* cppy is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* cppy is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with cppy.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <string>
using std::string;

struct global_namespace_struct
{
};

struct a_struct
{
    std::string j()
    {
        return "::a_struct::j";
    }
};

namespace test
{
    namespace inner
    {
        struct a_struct
        {
        };
    }

    struct a_struct
    {
        std::string f()
        {
            return "a_struct::f";
        }
    protected:
        std::string g()
        {
            return "a_struct::g";
        }
        virtual std::string h()
        {
            return "a_struct::h";
        }
    private:
        std::string i()
        {
            return "a_struct::i";
        }
    };

    class a_class
    {
        std::string f()
        {
            return "a_class::f";
        }
    protected:
        std::string g()
        {
            return "a_class::g";
        }
        virtual std::string h()
        {
            return "a_class::h";
        }
    public:
        std::string i()
        {
            return "a_class::i";
        }
    };

    class an_abstract_class
    {
    public:
        virtual std::string f()
        {
            return "an_abstract_class::f";
        }
        virtual std::string g() = 0;
    protected:
        std::string h()
        {
            return "an_abstract_class::h";
        }
    };

    class public_derived: public an_abstract_class
    {
    public:
        std::string g()
        {
            return "public_derived::g";
        }
    };

    class protected_derived: protected an_abstract_class
    {
    public:
        std::string g()
        {
            return "protected_derived::g";
        }
    };

    class private_derived: private an_abstract_class
    {
    public:
        std::string g()
        {
            return "private_derived::g";
        }
    };
}
