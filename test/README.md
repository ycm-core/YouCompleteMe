# Quick Start

## Running the tests in docker

To run the tests in the almost exactly the same environment as CI, use docker.
This is recommended to ensure that the tests pass in CI, rather than just on
your machine.

* Make sure you have docker installed (duh)
* Run `./docker/manual/run`.
* You should now be in the container. Your YCM checkout is now mounted in
  `$HOME/YouCompleteMe`
* Run the following setup:
  * `cd YouCompleteMe`
  * `python3 install.py --ts-completer --clangd-completer --java-completer`
  * `sudo -H pip3 install -r python/test_requirements.txt`
* Run the tests:
  * `./test/run_vim_tests`

## Running the tests locally

The CI tests run in [the container](#running-the-tests-in-docker), so it's
probably best to run your tests there too, but not strictly required.

To run locally, you have to be on MacOS or Linux. Sorry, Windows testing is
not supported. However, there is a [docker image](#running-the-tests-in-docker)
in which you can run the tests.

* Ensure you have at least the Vim vresion in YCM_VIM_VERSION (in
  `test/docker/ci/image/Dockerfile`)
* Ensure ycmd is compiled ***with python3*** and clangd is enabled
  `python3 install.py --ts-completer --clangd-completer --java-completer`
* Install the test python deps (`pip install -r python/test_requirements.txt`)
* Run `./test/run_vim_tests`

## Runniing the tests in Windows (WSL)

NOTE: This environment isn't officially supported, and the preferred mechanism to run the tests is to use docker.

* Install Ubuntu 20.04 WSL from Windows Store and launch it
* `sudo apt-get update && sudo apt-get dist-upgrade`
* `sudo apt-get install build-essential default-jdk vim-nox cmake python3-dev nodejs python3-pip npm`
* clone the plugin, and build ycmd, e.g.

```
git clone --recursive https://github.com/ycm-core/YouCompleteMe
cd YouCompleteMe
python3 install.py --ts-completer --clangd-completer --java-completer
```

* Install the test python deps: `pip3 install --user -r python/test_requirements.txt`
* Run `./test/run_vim_tests`

# Overview

The test framework is based on the "new style" Vim tests. These are the tests
that are used to test Vim itself. There is good info on this in `:help testing`.

There's also some useful info in Vim's test
[readme](https://github.com/vim/vim/blob/master/src/testdir/README.txt#L29).

In short, the test framework runs Vim, sources the test script, then executes
all of the test functions. This is done as follows :

```
vim --clean --not-a-term -S lib/run_test.vim <test script>.test.vim
```

The important thing to know is that `run_test.vim` is sourced and it in turn
sources the test script, which contains the test functions, which are named
`Test_*`.

Test functions should use the vim built-in `assert` functions to report errors
(see `:help new-style-testing`) and should attempt to reset any changes they
make at the end of the function.

You can add set-up and tear-down functions, and can skip tests by throwing a
message starting with the word 'Skipped' (e.g. `throw "SKipped: <message>"`).

# Test Framework

The test framework has the following components:

* A vim 'plugin' (in `test/lib`) containing the framework itself, comprising:
  * `run_test.vim`, which wraps the test functions and executes them, reporting
    failures.
  * Some basic support functions in `plugin/shared.vim` (from Vim)
  * Some screendump support functions in `plugin/screendump.vim` (from Vim)
  * Some YCM-specific autoloaded functions in `autoload/youcompleteme/test/*`
* A script to run the tests, including specific test script and function
* The actual test scripts in `test/*.test.vim`
* CI integration for azure.

# Test Scripts

The basic structure of a test is as follows:

```viml
function! SetUp()
  " ... set g:ycm_* options here...
  call youcompleteme#test#setup#SetUp()
endfunction

function! TearDown()
  call youcompleteme#test#setup#CleanUp()
endfunction

function! Test_MyTest()
  " test goes here, e.g.
  aseert_true( pyxeval( 'ycm_state.ServerIsHealthy()' ) )
endfunction

" Optional per-test setup/teardown
function! SetUp_Test_MyOtherTest()
  let s:old_ycm_use_clangd = g:ycm_use_clangd
  let g:ycm_use_clangd=1
endfunction

function! TearDown_Test_MyOtherTest()
  let g:ycm_use_clangd=s:old_ycm_use_clangd
endfunction

function! Test_MyOtherTest()
  assert_false( 0 )
endfunction
```

Test scripts are placed in `src/test` and are named `*.test.vim`. Each
test script can contain any number of individual tests, each of which is
a Vim function named `Test_<test name>`. Test functions are run in
arbitrary order, so must not rely on each other.

Each test script is a fixture, but setup and teardown is done for each and every
test. Global (one-time) setup can be done at script level, but this is not
recommended.

Set up and tear down functions are run before and after tests. You can
define one for the whole script, which is run before every test, and a
per-test setup/tear down function which is run before both the global
setup function and the test function. 

To explain, for each function in the script named `Test_<test name>`,
`run_test.vim` does the following:

* If there is a function named `SetUp_Test_<test name>`, call it
* If there is a function named `SetUp`, call it
* Call `Test_<test name>`
* If there is a function named `TearDown`, call it
* If there is a function named `TearDown_Test_<test name>`, call it

If the `v:errors` list is non-empty at the end of the tests, the test
`test name` is marked as failed.

If any of these functions raises an exception, it is added to `v:errors`, unless
the test is called `Test_nocatch_<test name>`, in which case exceptions are not
caught be the test and should be handled by the test function itself.

If a test fails, `run_test.vim` attempts to print out all of the log files that
YCM's `ycm_state` object knows about.

# The test plugin

The "plugin" provides a handful of things, some of which were simply ported from
Vim's test framework, and some were writted specifically for YCM.

## Ported from Vim

These are general purpose functions which are commonly used:

* `WaitForAssert`: This one is the most useful. It takes a callable (usually a
  lambda) and waits for it to return 0, but allows the Vim event loop to run in
  betwen calls. This is key to ensuring that the YCM code can execute while the
  script is actively trying to test it. **NOTE**: It waits for the _function to
  return 0_, **NOT** for the assert to be true/v:errors to be empty!

## YCM-specific

The autoload functions perform some useful common YCM-sepcific stuff such as
setup and teardown, and will likely be built out over time as the suite
increases in size and complexity.

# Tips and tricks

Things that you need to know to write tests effectively:

* Don't forget to `:%bwipeout!` at the end of each test function.

* Understand the arguments to `feedkeys`. Importantly, if you want it to behave
  the way you think it should, use `feedkey( "...", 'xt' )`. This makes it wait
  for the input to be actually read before returning, which is important for
  tests. See `:help feedkeys` for the other options.

* Remember that test scripts a vim functions. I know that sounds obvious, but
  things like "insert mode completions" are hard to test with functions which
  are typically *not* invoked in insert mode. In order to actually do anything
  in insert mode, you need to do the following:

  * If you want `TextChangedI` to fire,
    [call `test_override( 'char_avail', 1)`](https://github.com/vim/vim/issues/4665#event-2480928194)

  * Normally, `feedkeys` would exit insert mode if you enter it. Tell it not to
    by passing the `!` flag. 

  * Now that you've left Vim in insert mode, your test will hang forever unless
    you exit insert mode, so define a function and call it via a timer
    or other async callback which performs the actual asserts, and ends by
    calling `feedkeys( "\<ESC>" )` to exit insert mode.

  * Check `completion.test.vim` for an example.

* Remember that the `assert*` functions don't throw exceptions. They return `0`
  on success, and return nonzero on failure, populating `v:errors`. 

* Throwing exceptions in tests does fail the test, but this is not recommended
  because it skips the (local) teardown code.

* If you're writing a test function, it needs to conform as follows:
  * Only adding to `v:errors` (e.g. `call add(v:errors, 'test')`) will cause the
    test to fail.
  * Don't throw exceptions. This will cause fiddly issues.
  * Return `0` on success and `1` on failure. This allows it to be used with
    `WaitForAssert`

# Restricting what is run

`run_vim_tests` takes arguments of the form `<test script>:<test function filter>`.

For eample to just run the "MyOtherTest" test in the `mytests.test.vim`:

```
$ run_vim_tests mytests.test.vim:MyOtherTest
```

The filter is a Vim regexp. The same script file can be listed multiple times,
as in:

```
$ run_vim_tests 'mytests.test.vim:MyTest' 'mytests.test.vim:MyOtherTest'
```

# Coverage

The test suite supports `covimerage` coverage testing. Just set the `COVERAGE`
environment variable when running `run_vim_tests`.

This generates coverage for both the python code and the vimscript code.

For python, there is some initialisation code in `run_test.vim` which starts up
`coverage` and saves the result to `.coverage.python`.

For vim script, we use `covimerage` which takes the vim `:profile` data (also
initialised in `run_test.vim`) and converts it to `coverage`-style data in
`.coverage.vim` (this is done by `run_vim_tests` after running all the tests).

Finally, we upload that data to `codecov`. This combines `.coverage.python` and
`.coverage.vim` into `.coverage` and uploads it.

To get a local summary:

* `pip install --user -r python/test_requirements.txt`
* `COVERAGE=true ./test/run_vim_tests`
* `coverage combine -a`
* `coverage report` or `coverage html`

# Docker

We generate and push 2 containers:

* `youcompleteme/ycm-vim-py3:test` and `youcompleteme/ycm-vim-py3:manual`

The `:test` tags are the containers that are used by Azure pipelines to run the
tests and contains essentially Ubuntu LTS + the YCM dependencies and a build of
Vim at a specific version built with python3 (`-py3`) support.

The `:manual` tags extend the `:test` tags with a user account that largely
matches the one created by Azure to run our tests. It also installs a basic
`vimrc` so that you can do manual testing too.

## Building

To rebuild and push all of the containers: 

* `cd test/docker`
* `./rebuild_all`

This script essentially runs `./rebuild` and `./push` in each of the `ci` and
`manual` directories (corresponding to the `:test` and `:manual` tags
respectively). 

Those scripts are just simple wrappers for `docker build` and `docker push`
because it's easy to forget the exact syntax.
