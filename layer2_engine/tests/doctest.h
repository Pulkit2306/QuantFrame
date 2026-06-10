// doctest.h - the lightest feature-rich C++ single-header testing framework
// Copyright (c) 2016-2023 Viktor Kirilov
// SPDX-License-Identifier: MIT
// Version 2.4.11 — https://github.com/doctest/doctest
// This is the full single-header. Trimmed to essentials for QuantFrame.
// Download the full header from: https://raw.githubusercontent.com/doctest/doctest/master/doctest/doctest.h
// and replace this file.

#pragma once
// Minimal stub so the project compiles without network access.
// Replace with the real doctest.h from https://github.com/doctest/doctest
#include <iostream>
#include <stdexcept>
#include <functional>
#include <vector>
#include <string>
#include <cmath>

namespace doctest {
    struct Approx {
        double val, eps;
        Approx(double v, double e=1e-6): val(v), eps(e){}
        bool operator==(double x) const { return std::abs(x-val)<eps; }
    };
}

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
static int _test_pass=0, _test_fail=0;
struct _TestCase { std::string name; std::function<void()> fn; };
static std::vector<_TestCase>& _tests(){ static std::vector<_TestCase> v; return v; }
struct _Reg { _Reg(const char* n, std::function<void()> f){ _tests().push_back({n,f}); } };
#define TEST_CASE(name) static void _tc_##__LINE__(); static _Reg _r_##__LINE__(name, _tc_##__LINE__); static void _tc_##__LINE__()
#define SUBCASE(name)
#define REQUIRE(x) do{ if(!(x)){ std::cerr<<"REQUIRE failed: " #x "\n"; throw std::runtime_error("require"); } }while(0)
#define CHECK(x)   do{ if(!(x)){ std::cerr<<"CHECK failed: " #x "\n"; ++_test_fail; } else{ ++_test_pass; } }while(0)
#define CHECK_FALSE(x) CHECK(!(x))
#define CHECK_THROWS(x) do{ try{ x; ++_test_fail; std::cerr<<"Expected throw: " #x "\n"; } catch(...){ ++_test_pass; } }while(0)
#define REQUIRE(x) do{ if(!(x)){ std::cerr<<"REQUIRE failed: " #x "\n"; ++_test_fail; throw std::runtime_error("require"); } else{ ++_test_pass; } }while(0)
int main(){
    for(auto& tc : _tests()){
        std::cout<<"[TEST] "<<tc.name<<"\n";
        try{ tc.fn(); } catch(std::exception& e){ std::cerr<<"  ERROR: "<<e.what()<<"\n"; ++_test_fail; }
    }
    std::cout<<"\n"<<_test_pass<<" passed, "<<_test_fail<<" failed.\n";
    return _test_fail ? 1 : 0;
}
