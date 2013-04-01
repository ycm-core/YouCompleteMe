struct Foo {
  int bar;
  int zoo;
};

struct Bar {
  int foo;
  int zoo;
};

struct Foo;
struct Zoo;

void func() {
  Foo foo;
  foo.bar = 5;
  Zoo *zoo = 0;
}
