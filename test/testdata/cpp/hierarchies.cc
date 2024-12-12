int f();

int g() {
    return f() + f();
}

int h() {
    int x = g();
    return f() + x;
}

struct B0 {};
struct B1 : B0 {};

struct D0 : B0 {};
struct D1 : B0, B1 {};
