YouCompleteMe: a code-completion engine for Vim
===============================================

[![Gitter room](https://img.shields.io/gitter/room/Valloric/YouCompleteMe.svg)](https://gitter.im/Valloric/YouCompleteMe)
[![Linux build status](https://img.shields.io/travis/Valloric/YouCompleteMe/master.svg?label=Linux)](https://travis-ci.org/Valloric/YouCompleteMe)
[![macOS build status](https://img.shields.io/circleci/project/github/Valloric/YouCompleteMe/master.svg?label=macOS)](https://circleci.com/gh/Valloric/YouCompleteMe)
[![Windows build status](https://img.shields.io/appveyor/ci/Valloric/YouCompleteMe/master.svg?label=Windows)](https://ci.appveyor.com/project/Valloric/YouCompleteMe)
[![Coverage status](https://img.shields.io/codecov/c/github/Valloric/YouCompleteMe/master.svg)](https://codecov.io/gh/Valloric/YouCompleteMe)

Help, Advice, Support
---------------------

Looking for help, advice or support? Having problems getting YCM to work?

First carefully read the [installation instructions](#installation) for your OS.
We recommend you use the supplied `install.py`.

Next check the [User Guide](#user-guide) section on the semantic completer that
you are using. For C/C++/Objective-C/Objective-C++/CUDA, you  _must_ read [this
section](#c-family-semantic-completion).

Finally, check the [FAQ](#faq).

If, after reading the installation and user guides, and checking the FAQ, you're
still having trouble, check the [contacts](#contact) section below for how to
get in touch.

Please do **NOT** go to #vim on freenode for support. Please contact the
YouCompleteMe maintainers directly using the [contact details](#contact) below.

Contents
--------

- [Intro](#intro)
- [Installation](#installation)
    - [Mac OS X](#mac-os-x)
    - [Linux 64-bit](#linux-64-bit)
    - [Windows](#windows)
    - [FreeBSD/OpenBSD](#freebsdopenbsd)
    - [Full Installation Guide](#full-installation-guide)
- [Quick Feature Summary](#quick-feature-summary)
- [User Guide](#user-guide)
    - [General Usage](#general-usage)
    - [Client-Server Architecture](#client-server-architecture)
    - [Completion String Ranking](#completion-string-ranking)
    - [General Semantic Completion](#general-semantic-completion)
    - [C-family Semantic Completion](#c-family-semantic-completion)
    - [Java Semantic Completion](#java-semantic-completion)
    - [Python Semantic Completion](#python-semantic-completion)
    - [Rust Semantic Completion](#rust-semantic-completion)
    - [JavaScript and TypeScript Semantic Completion](#javascript-and-typescript-semantic-completion)
    - [Semantic Completion for Other Languages](#semantic-completion-for-other-languages)
    - [Writing New Semantic Completers](#writing-new-semantic-completers)
    - [Diagnostic Display](#diagnostic-display)
        - [Diagnostic Highlighting Groups](#diagnostic-highlighting-groups)
- [Commands](#commands)
    - [YcmCompleter subcommands](#ycmcompleter-subcommands)
        - [GoTo Commands](#goto-commands)
        - [Semantic Information Commands](#semantic-information-commands)
        - [Refactoring Commands](#refactoring-commands)
        - [Miscellaneous Commands](#miscellaneous-commands)
- [Functions](#functions)
- [Autocommands](#autocommands)
- [Options](#options)
- [FAQ](#faq)
- [Contributor Code of Conduct](#contributor-code-of-conduct)
- [Contact](#contact)
- [License](#license)


Intro
-----

YouCompleteMe is a fast, as-you-type, fuzzy-search code completion engine for
[Vim][]. It has several completion engines:

- an identifier-based engine that works with every programming language,
- a [Clang][]-based engine that provides native semantic code
  completion for C/C++/Objective-C/Objective-C++/CUDA (from now on referred to
  as "the C-family languages"),
- a [clangd][]-based **experimental** completion engine for the C-family
  languages.
- a [Jedi][]-based completion engine for Python 2 and 3,
- an [OmniSharp][]-based completion engine for C#,
- a combination of [Gocode][] and [Godef][] semantic engines for Go,
- a [TSServer][]-based completion engine for JavaScript and TypeScript,
- a [racer][]-based completion engine for Rust,
- a [jdt.ls][]-based experimental completion engine for Java.
- and an omnifunc-based completer that uses data from Vim's omnicomplete system
  to provide semantic completions for many other languages (Ruby, PHP etc.).

![YouCompleteMe GIF demo](http://i.imgur.com/0OP4ood.gif)

Here's an explanation of what happens in the short GIF demo above.

First, realize that **no keyboard shortcuts had to be pressed** to get the list
of completion candidates at any point in the demo. The user just types and the
suggestions pop up by themselves. If the user doesn't find the completion
suggestions relevant and/or just wants to type, they can do so; the completion
engine will not interfere.

When the user sees a useful completion string being offered, they press the TAB
key to accept it. This inserts the completion string. Repeated presses of the
TAB key cycle through the offered completions.

If the offered completions are not relevant enough, the user can continue typing
to further filter out unwanted completions.

A critical thing to notice is that the completion **filtering is NOT based on
the input being a string prefix of the completion** (but that works too). The
input needs to be a _[subsequence][] match_ of a completion. This is a fancy way
of saying that any input characters need to be present in a completion string in
the order in which they appear in the input. So `abc` is a subsequence of
`xaybgc`, but not of `xbyxaxxc`. After the filter, a complicated sorting system
ranks the completion strings so that the most relevant ones rise to the top of
the menu (so you usually need to press TAB just once).

**All of the above works with any programming language** because of the
identifier-based completion engine. It collects all of the identifiers in the
current file and other files you visit (and your tags files) and searches them
when you type (identifiers are put into per-filetype groups).

The demo also shows the semantic engine in use. When the user presses `.`, `->`
or `::` while typing in insert mode (for C++; different triggers are used for
other languages), the semantic engine is triggered (it can also be triggered
with a keyboard shortcut; see the rest of the docs).

The last thing that you can see in the demo is YCM's diagnostic display features
(the little red X that shows up in the left gutter; inspired by [Syntastic][])
if you are editing a C-family file. As the completer engine compiles your file
and detects warnings or errors, they will be presented in various ways. You
don't need to save your file or press any keyboard shortcut to trigger this, it
"just happens" in the background.

In essence, YCM obsoletes the following Vim plugins because it has all of their
features plus extra:

- clang_complete
- AutoComplPop
- Supertab
- neocomplcache

**And that's not all...**

YCM also provides [semantic IDE-like features](#quick-feature-summary) in a
number of languages, including:

- finding declarations, definitions, usages, etc. of identifiers,
- displaying type information for classes, variables, functions etc.,
- displaying documentation for methods, members, etc. in the preview window,
- fixing common coding errors, like missing semi-colons, typos, etc.,
- semantic renaming of variables across files,
- formatting code,
- removing unused imports, sorting imports, etc.

Features vary by file type, so make sure to check out the [file type feature
summary](#quick-feature-summary) and the
[full list of completer subcommands](#ycmcompleter-subcommands) to
find out what's available for your favourite languages.

You'll also find that YCM has filepath completers (try typing `./` in a file)
and a completer that integrates with [UltiSnips][].

Installation
------------

### Mac OS X

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

Install the latest version of [MacVim][]. Yes, MacVim. And yes, the _latest_.

If you don't use the MacVim GUI, it is recommended to use the Vim binary that is
inside the MacVim.app package (`MacVim.app/Contents/MacOS/Vim`). To ensure it
works correctly copy the `mvim` script from the [MacVim][] download to your
local binary folder (for example `/usr/local/bin/mvim`) and then symlink it:

    ln -s /usr/local/bin/mvim vim

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

**NOTE:** If you want C-family completion, you MUST have the latest Xcode
installed along with the latest Command Line Tools (they are installed
automatically when you run `clang` for the first time, or manually by running
`xcode-select --install`)

Install CMake. Preferably with [Homebrew][brew], but here's the [stand-alone
CMake installer][cmake-download].

_If_ you have installed a Homebrew Python and/or Homebrew MacVim, see the _FAQ_
for details.

Compiling YCM **with** semantic support for C-family languages through
**libclang**:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --clang-completer

Compiling YCM **with** semantic support for C-family languages through
**experimental clangd**:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --clangd-completer

Note that you can install YCM with both **libclang** and **clangd** enabled. In
that case **clangd** will be preferred unless you have the following in your
`vimrc`:

```viml
let g:ycm_use_clangd = 0
```

Compiling YCM **without** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py

The following additional language support options are available:

- C# support: install Mono with [Homebrew][brew] or by downloading the [Mono Mac
  package][mono-install-osx] and add `--cs-completer` when calling
  `install.py`.
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: install [Rust][rust-install] and add
  `--rust-completer` when calling `install.py`.
- Java support: install [JDK8 (version 8 required)][jdk-install] and add
  `--java-completer` when calling `install.py`.

To simply compile with everything enabled, there's a `--all` flag. Note that
this flag does **not** install **clangd**. You need to specify it manually by
adding `--clangd-completer`. So, to install with all language features, ensure
`xbuild`, `go`, `tsserver`, `node`, `npm`, `rustc`, and `cargo` tools are
installed and in your `PATH`, then simply run:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --all

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### Linux 64-bit

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

Make sure you have Vim 7.4.1578 with Python 2 or Python 3 support. The Vim
package on Fedora 27 and later and the pre-installed Vim on Ubuntu 16.04 and
later are recent enough. You can see the version of Vim installed by running
`vim --version`. If the version is too old, you may need to [compile Vim from
source][vim-build] (don't worry, it's easy).

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library APIs have changed (happens rarely), YCM
will notify you to recompile it. You should then rerun the install process.

Install development tools, CMake, and Python headers:

- Fedora 27 and later:

      sudo dnf install cmake gcc-c++ make python3-devel

- Ubuntu 14.04:

      sudo apt install build-essential cmake3 python3-dev

- Ubuntu 16.04 and later:

      sudo apt install build-essential cmake python3-dev

Compiling YCM **with** semantic support for C-family languages through
**libclang**:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --clang-completer

Compiling YCM **with** semantic support for C-family languages through
**experimental clangd**:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --clangd-completer

Note that you can install YCM with both **libclang** and **clangd** enabled. In
that case **clangd** will be preferred unless you have the following in your
`vimrc`:

```viml
let g:ycm_use_clangd = 0
```

Compiling YCM **without** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    python3 install.py

The following additional language support options are available:

- C# support: install [Mono][mono-install-linux] and add `--cs-completer`
  when calling `install.py`.
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: install [Rust][rust-install] and add `--rust-completer` when
  calling `install.py`.
- Java support: install [JDK8 (version 8 required)][jdk-install] and add
  `--java-completer` when calling `install.py`.

To simply compile with everything enabled, there's a `--all` flag. Note that
this flag does **not** install **clangd**. You need to specify it manually by
adding `--clangd-completer`. So, to install with all language features, ensure
`xbuild`, `go`, `tsserver`, `node`, `npm`, `rustc`, and `cargo` tools are
installed and in your `PATH`, then simply run:

    cd ~/.vim/bundle/YouCompleteMe
    python3 install.py --all

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### Windows

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

**Important:** we assume that you are using the `cmd.exe` command prompt and
that you know how to add an executable to the PATH environment variable.

Make sure you have at least Vim 7.4.1578 with Python 2 or Python 3 support. You
can check the version and which Python is supported by typing `:version` inside
Vim. Look at the features included: `+python/dyn` for Python 2 and
`+python3/dyn` for Python 3. Take note of the Vim architecture, i.e. 32 or
64-bit. It will be important when choosing the Python installer. We recommend
using a 64-bit client. [Daily updated installers of 32-bit and 64-bit Vim with
Python 2 and Python 3 support][vim-win-download] are available.

Add the line:

    set encoding=utf-8

to your [vimrc][] if not already present. This option is required by YCM. Note
that it does not prevent you from editing a file in another encoding than UTF-8.
You can do that by specifying [the `++enc` argument][++enc] to the `:e` command.

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

Download and install the following software:

- [Python 2 or Python 3][python-win-download]. Be sure to pick the version
  corresponding to your Vim architecture. It is _Windows x86_ for a 32-bit Vim
  and _Windows x86-64_ for a 64-bit Vim. We recommend installing Python 3.
  Additionally, the version of Python you install must match up exactly with
  the version of Python that Vim is looking for. Type `:version` and look at the
  bottom of the page at the list of compiler flags. Look for flags that look
  similar to `-DDYNAMIC_PYTHON_DLL=\"python27.dll\"` and
  `-DDYNAMIC_PYTHON3_DLL=\"python35.dll\"`. The former indicates that Vim is
  looking for Python 2.7 and the latter indicates that Vim is looking for
  Python 3.5. You'll need one or the other installed, matching the version
  number exactly.
- [CMake][cmake-download]. Add CMake executable to the PATH environment
  variable.
- [Visual Studio][visual-studio-download]. Download the community edition.
  During setup, select _Desktop development with C++_ in _Workloads_.

Compiling YCM **with** semantic support for C-family languages through
**libclang**:

    cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
    python install.py --clang-completer

Compiling YCM **with** semantic support for C-family languages through
**experimental clangd**:

    cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
    python install.py --clangd-completer

Note that you can install YCM with both **libclang** and **clangd** enabled. In
that case **clangd** will be preferred unless you have the following in your
`vimrc`:

```viml
let g:ycm_use_clangd = 0
```

Compiling YCM **without** semantic support for C-family languages:

    cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
    python install.py

The following additional language support options are available:

- C# support: add `--cs-completer` when calling `install.py`.
  Be sure that [the build utility `msbuild` is in your PATH][add-msbuild-to-path].
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: install [Rust][rust-install] and add `--rust-completer` when
  calling `install.py`.
- Java support: install [JDK8 (version 8 required)][jdk-install] and add
  `--java-completer` when calling `install.py`.

To simply compile with everything enabled, there's a `--all` flag. Note that
this flag does **not** install **clangd**. You need to specify it manually by
adding `--clangd-completer`. So, to install with all language features, ensure
`msbuild`, `go`, `tsserver`, `node`, `npm`, and `cargo` tools are installed and
in your `PATH`, then simply run:

    cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
    python install.py --all

You can specify the Microsoft Visual C++ (MSVC) version using the `--msvc`
option. YCM officially supports MSVC 14 (Visual Studio 2015) and 15 (2017).

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### FreeBSD/OpenBSD

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

**NOTE:** OpenBSD / FreeBSD are not officially supported platforms by YCM.

Make sure you have Vim 7.4.1578 with Python 2 or Python 3 support.

OpenBSD 5.5 and later have a Vim that's recent enough. You can see the version of
Vim installed by running `vim --version`.

For FreeBSD 11.x, the requirement is cmake:

    pkg install cmake

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

Compiling YCM **with** semantic support for C-family languages through
**libclang**:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --clang-completer

Compiling YCM **with** semantic support for C-family languages through
**experimental clangd**:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --clangd-completer

Note that you can install YCM with both **libclang** and **clangd** enabled. In
that case **clangd** will be preferred unless you have the following in your
`vimrc`:

```viml
let g:ycm_use_clangd = 0
```

Compiling YCM **without** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py

If the `python` executable is not present, or the default `python` is not the
one that should be compiled against, specify the python interpreter explicitly:

    python3 install.py --clang-completer

The following additional language support options are available:

- C# support: install Mono and add `--cs-completer` when calling
  `./install.py`.
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `./install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: install [Rust][rust-install] and add `--rust-completer` when
  calling `./install.py`.
- Java support: install [JDK8 (version 8 required)][jdk-install] and add
  `--java-completer` when calling `./install.py`.

To simply compile with everything enabled, there's a `--all` flag. Note that
this flag does **not** install **clangd**. You need to specify it manually by
adding `--clangd-completer`. So, to install with all language features, ensure
`xbuild`, `go`, `tsserver`, `node`, `npm`, `rustc`, and `cargo` tools are
installed and in your `PATH`, then simply run:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.py --all

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### Full Installation Guide

These are the steps necessary to get YCM working on a Unix OS and on Windows.

**Note to Windows users:** we assume that you are running the `cmd.exe` command
prompt and that the needed executables are in the PATH environment variable. Do
not just copy the shell commands. Replace `~` by `%USERPROFILE%` in them and use
the right Vim home directory. It should be `vimfiles` by default instead of
`.vim`.

See the _FAQ_ if you have any issues.

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

**Please follow the instructions carefully. Read EVERY WORD.**

1.  **Ensure that your version of Vim is _at least_ 7.4.1578 _and_ that it has
    support for Python 2 or Python 3 scripting**.

    Inside Vim, type `:version`. Look at the first two to three lines of output;
    it should say `Vi IMproved X.Y`, where X.Y is the major version of vim. If
    your version is greater than 7.4, then you're all set. If your version is
    7.4 then look below that where it says, `Included patches: 1-Z`, where Z
    will be some number. That number needs to be 1578 or higher.

    If your version of Vim is not recent enough, you may need to [compile Vim
    from source][vim-build] (don't worry, it's easy).

    After you have made sure that you have Vim 7.4.1578+, type the following in
    Vim: `:echo has('python') || has('python3')`. The output should be 1. If
    it's 0, then get a version of Vim with Python support.

    On Windows, check also if your Vim architecture is 32 or 64-bit. This is
    critical because it must match the Python and the YCM libraries
    architectures. We recommend using a 64-bit Vim.

2.  **Install YCM** with [Vundle][] (or [Pathogen][], but Vundle is a better
    idea). With Vundle, this would mean adding a `Plugin
    'Valloric/YouCompleteMe'` line to your [vimrc][].

    If you don't install YCM with Vundle, make sure you have run
    `git submodule update --init --recursive` after checking out the YCM
    repository (Vundle will do this for you) to fetch YCM's dependencies.

3.  *Complete this step ONLY if you care about semantic completion support for
    C-family languages. Otherwise it's not necessary.*

    **Download the latest version of `libclang`**. Clang is an open-source
    compiler that can compile C-family languages. The `libclang` library it
    provides is used to power the YCM semantic completion engine for those
    languages. YCM is designed to work with libclang version 7.0.0 or higher.

    In addition to `libclang`, YCM also supports an **experimental**
    [clangd][]-based completer. You can download the latest version of
    [clangd][] from [llvm.org releases][clang-download]. Follow Step 4 to learn
    how to tell YCM where to find clangd binary. Please note that YCM is
    designed to work with [clangd][] version 7.0.0 or higher.

    You can use the system libclang or clangd _only if you are sure it is
    version 7.0.0 or higher_, otherwise don't. Even if it is, we recommend using
    the [official binaries from llvm.org][clang-download] if at all possible.
    Make sure you download the correct archive file for your OS.

    We **STRONGLY recommend AGAINST use** of the system libclang or clangd
    instead of the upstream compiled binaries. Random things may break. Save
    yourself the hassle and use the upstream pre-built libclang or clangd.

4.  **Compile the `ycm_core` library** that YCM needs. This library
    is the C++ engine that YCM uses to get fast completions.

    You will need to have `cmake` installed in order to generate the required
    makefiles. Linux users can install cmake with their package manager (`sudo
    apt-get install cmake` for Ubuntu) whereas other users can [download and
    install][cmake-download] cmake from its project site. Mac users can also get
    it through [Homebrew][brew] with `brew install cmake`.

    On a Unix OS, you need to make sure you have Python headers installed. On a
    Debian-like Linux distro, this would be `sudo apt-get install python-dev
    python3-dev`. On Mac they should already be present.

    On Windows, you need to download and install [Python 2 or
    Python 3][python-win-download]. Pick the version corresponding to your Vim
    architecture. You will also need Microsoft Visual C++ (MSVC) to build YCM.
    You can obtain it by installing [Visual Studio][visual-studio-download].
    MSVC 14 (Visual Studio 2015) and 15 (2017) are officially supported.

    Here we'll assume you installed YCM with Vundle. That means that the
    top-level YCM directory is in `~/.vim/bundle/YouCompleteMe`.

    We'll create a new folder where build files will be placed. Run the
    following:

        cd ~
        mkdir ycm_build
        cd ycm_build

    Now we need to generate the makefiles. If you DON'T care about semantic
    support for C-family languages or plan to use **experimental** [clangd][]
    based completer, run the following command in the `ycm_build` directory:

        cmake -G "<generator>" . ~/.vim/bundle/YouCompleteMe/third_party/ycmd/cpp

    where `<generator>` is `Unix Makefiles` on Unix systems and one of the
    following Visual Studio generators on Windows:

    - `Visual Studio 14 Win64`
    - `Visual Studio 15 Win64`

    Remove the `Win64` part in these generators if your Vim architecture is
    32-bit.

    For those who want to use the system version of boost, you would pass
    `-DUSE_SYSTEM_BOOST=ON` to cmake. This may be necessary on some systems
    where the bundled version of boost doesn't compile out of the box.

    **NOTE:** We **STRONGLY recommend AGAINST use** of the system boost instead
    of the bundled version of boost. Random things may break. Save yourself
    the hassle and use the bundled version of boost.

    If you DO care about semantic support for C-family languages, and want to
    use libclang as the provider instead of **experimental** [clangd][]-based
    completer then your `cmake` call will be a bit more complicated. We'll
    assume you downloaded a binary distribution of LLVM+Clang from llvm.org in
    step 3 and that you extracted the archive file to folder
    `~/ycm_temp/llvm_root_dir` (with `bin`, `lib`, `include` etc. folders right
    inside that folder). On Windows, you can extract the files from the
    LLVM+Clang installer using [7-zip][7z-download].

    **NOTE:** This _only_ works with a _downloaded_ LLVM binary package, not a
    custom-built LLVM! See docs below for `EXTERNAL_LIBCLANG_PATH` when using a
    custom LLVM build.

    With that in mind, run the following command in the `ycm_build` directory:

        cmake -G "<generator>" -DPATH_TO_LLVM_ROOT=~/ycm_temp/llvm_root_dir . ~/.vim/bundle/YouCompleteMe/third_party/ycmd/cpp

    where `<generator>` is replaced like above.

    Now that configuration files have been generated, compile the libraries
    using this command:

        cmake --build . --target ycm_core --config Release

    The `--config Release` part is specific to Windows and will be ignored on a
    Unix OS.

    For those who want to use the system version of libclang, you would pass
    `-DUSE_SYSTEM_LIBCLANG=ON` to cmake _instead of_ the
    `-DPATH_TO_LLVM_ROOT=...` flag.

    **NOTE:** We **STRONGLY recommend AGAINST use** of the system libclang instead
    of the upstream compiled binaries. Random things may break. Save yourself
    the hassle and use the upstream pre-built libclang.

    You could also force the use of a custom libclang library with
    `-DEXTERNAL_LIBCLANG_PATH=/path/to/libclang.so` flag (the library would end
    with `.dylib` on a Mac). Again, this flag would be used _instead of_ the
    other flags. **If you compiled LLVM from source, this is the flag you should
    be using.**

    Running the `cmake` command will also place the `libclang.[so|dylib|dll]` in
    the `YouCompleteMe/third_party/ycmd` folder for you if you compiled with
    clang support (it needs to be there for YCM to work).

    If you DO care about semantic support for C-family languages, and want to
    use **experimental** [clangd][]-based completer then you need to add
    following line to your `vimrc`:
    ```viml
    let g:ycm_clangd_binary_path = "/path/to/clangd"
    ```
    You need to change `/path/to/clangd` with the path of binary you downloaded
    in step 3.

5.  *This step is optional.*

    Build the [regex][] module for improved Unicode support and better
    performance with regular expressions. The procedure is similar to compiling
    the `ycm_core` library:

        cd ~
        mkdir regex_build
        cd regex_build
        cmake -G "<generator>" . ~/.vim/bundle/YouCompleteMe/third_party/ycmd/third_party/cregex
        cmake --build . --target _regex --config Release

    where `<generator>` is the same generator used in the previous step.

6.  Set up support for additional languages, as desired:

    - C# support: install [Mono on non-Windows platforms][mono-install].
      Navigate to `YouCompleteMe/third_party/ycmd/third_party/OmniSharpServer`
      and run

          msbuild /property:Configuration=Release /property:Platform="Any CPU" /property:TargetFrameworkVersion=v4.5

      On Windows, be sure that [the build utility `msbuild` is in your
      PATH][add-msbuild-to-path].

    - Go support: install [Go][go-install] and add it to your path. Navigate to
      `YouCompleteMe/third_party/ycmd/third_party/go` and in **both**
      `src/github.com/mdempsky/gocode` and `src/github.com/rogpeppe/godef` run

          GOPATH=$(realpath ../../../..) go build

      On Windows, first set `GOPATH` to the absolute path of
      `YouCompleteMe/third_party/ycmd/third_party/go` then run `go build` in the two
      directories above.

    - JavaScript and TypeScript support: install [Node.js and npm][npm-install],
      navigate to `YouCompleteMe/third_party/ycmd` and run
      `npm install -g --prefix third_party/tsserver typescript`.

    - Rust support: install [Rust][rust-install]. Navigate to
      `YouCompleteMe/third_party/ycmd/third_party/racerd` and run `cargo build
      --release`.

    - Java support: install [JDK8 (version 8 required)][jdk-install]. Download a
      [binary release of eclipse.jdt.ls][jdtls-release] and extract it to
      `YouCompleteMe/third_party/ycmd/third_party/eclipse.jdt.ls/target/repository`.
      Note: this approach is not recommended for most users and is supported
      only for advanced users and developers of YCM on a best-efforts basis.
      Please use `install.py` to enable java support.

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

Quick Feature Summary
-----

### General (all languages)

* Super-fast identifier completer including tags files and syntax elements
* Intelligent suggestion ranking and filtering
* File and path suggestions
* Suggestions from Vim's OmniFunc
* UltiSnips snippet suggestions

### C-family languages (C, C++, Objective C, Objective C++, CUDA)

* Semantic auto-completion with automatic fixes
* Real-time diagnostic display
* Go to include/declaration/definition (`GoTo`, etc.)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors (`FixIt`)

### C♯

* Semantic auto-completion
* Real-time diagnostic display
* Go to declaration/definition (`GoTo`, etc.)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors (`FixIt`)
* Management of OmniSharp server instance

### Python

* Semantic auto-completion
* Go to definition (`GoTo`)
* Reference finding (`GoToReferences`)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)

### Go

* Semantic auto-completion
* Go to definition (`GoTo`)
* Management of `gocode` server instance

### JavaScript and TypeScript

* Semantic auto-completion with automatic import insertion
* Real-time diagnostic display
* Go to definition (`GoTo`, `GoToDefinition`, and `GoToDeclaration` are
  identical)
* Go to type definition (`GoToType`)
* Reference finding (`GoToReferences`)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors (`FixIt`)
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)
* Organize imports (`OrganizeImports`)
* Management of `TSServer` server instance

### Rust

* Semantic auto-completion
* Go to definition (`GoTo`, `GoToDefinition`, and `GoToDeclaration` are
  identical)
* View documentation comments for identifiers (`GetDoc`)
* Management of `racer` server instance

### Java

**NOTE**: Java support is currently experimental. Please let us know your
[feedback](#contact).

* Semantic auto-completion with automatic import insertion
* Real-time diagnostic display
* Go to definition (`GoTo`, `GoToDefinition`, and `GoToDeclaration` are
  identical)
* Reference finding (`GoToReferences`)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors including code generation (`FixIt`)
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)
* Organize imports (`OrganizeImports`)
* Detection of java projects
* Management of `jdt.ls` server instance

User Guide
----------

### General Usage

If the offered completions are too broad, keep typing characters; YCM will
continue refining the offered completions based on your input.

Filtering is "smart-case" and "smart-[diacritic][]" sensitive; if you are
typing only lowercase letters, then it's case-insensitive. If your input
contains uppercase letters, then the uppercase letters in your query must
match uppercase letters in the completion strings (the lowercase letters still
match both). On top of that, a letter with no diacritic marks will match that
letter with or without marks:

<table>
<tbody>
<tr>
  <th>matches</th>
  <th>foo</th>
  <th>fôo</th>
  <th>fOo</th>
  <th>fÔo</th>
</tr>
<tr>
  <th>foo</th>
  <td>✔️</td>
  <td>✔️</td>
  <td>✔️</td>
  <td>✔️</td>
</tr>
<tr>
  <th>fôo</th>
  <td>❌</td>
  <td>✔️</td>
  <td>❌</td>
  <td>✔️</td>
</tr>
<tr>
  <th>fOo</th>
  <td>❌</td>
  <td>❌</td>
  <td>✔️</td>
  <td>✔️</td>
</tr>
<tr>
  <th>fÔo</th>
  <td>❌</td>
  <td>❌</td>
  <td>❌</td>
  <td>✔️</td>
</tr>
</tbody>
</table>

Use the TAB key to accept a completion and continue pressing TAB to cycle
through the completions. Use Shift-TAB to cycle backwards. Note that if you're
using console Vim (that is, not Gvim or MacVim) then it's likely that the
Shift-TAB binding will not work because the console will not pass it to Vim.
You can remap the keys; see the [Options](#options) section below.

Knowing a little bit about how YCM works internally will prevent confusion. YCM
has several completion engines: an identifier-based completer that collects all
of the identifiers in the current file and other files you visit (and your tags
files) and searches them when you type (identifiers are put into per-filetype
groups).

There are also several semantic engines in YCM. There are libclang-based and
clangd-based completers that provide semantic completion for C-family languages.
There's a Jedi-based completer for semantic completion for Python. There's also
an omnifunc-based completer that uses data from Vim's omnicomplete system to
provide semantic completions when no native completer exists for that language
in YCM.

There are also other completion engines, like the UltiSnips completer and the
filepath completer.

YCM automatically detects which completion engine would be the best in any
situation. On occasion, it queries several of them at once, merges the
outputs and presents the results to you.

### Client-Server Architecture

YCM has a client-server architecture; the Vim part of YCM is only a thin client
that talks to the [ycmd HTTP+JSON server][ycmd] that has the vast majority of
YCM logic and functionality. The server is started and stopped automatically as
you start and stop Vim.

### Completion String Ranking

The subsequence filter removes any completions that do not match the input, but
then the sorting system kicks in. It's actually very complicated and uses lots
of factors, but suffice it to say that "word boundary" (WB) subsequence
character matches are "worth" more than non-WB matches. In effect, this means
given an input of "gua", the completion "getUserAccount" would be ranked higher
in the list than the "Fooguxa" completion (both of which are subsequence
matches). A word-boundary character are all capital characters, characters
preceded by an underscore and the first letter character in the completion
string.

### General Semantic Completion

You can use Ctrl+Space to trigger the completion suggestions anywhere, even
without a string prefix. This is useful to see which top-level functions are
available for use.

### C-family Semantic Completion

In order to perform semantic analysis such as code completion, `GoTo` and
diagnostics, YouCompleteMe uses `libclang` or `clangd`. Both of them make use of
clang compiler, sometimes also referred to as llvm. Like any compiler,
clang also requires a set of compile flags in order to parse your code. Simply
put: If clang can't parse your code, YouCompleteMe can't provide semantic
analysis.

There are 2 methods which can be used to provide compile flags to clang:

#### Option 1: Use a [compilation database][compdb]

The easiest way to get YCM to compile your code is to use a compilation
database.  A compilation database is usually generated by your build system
(e.g. `CMake`) and contains the compiler invocation for each compilation unit in
your project.

For information on how to generate a compilation database, see the [clang
documentation][compdb]. In short:

- If using CMake, add `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` when configuring (or
  add `set( CMAKE_EXPORT_COMPILE_COMMANDS ON )` to `CMakeLists.txt`) and copy or
  symlink the generated database to the root of your project.
- If using Ninja, check out the `compdb` tool (`-t compdb`) in its
  [docs][ninja-compdb].
- If using GNU make, check out [Bear][].
- For other build systems, check out
  [`.ycm_extra_conf.py`](#option-2-provide-the-flags-manually) below. Note that
  **experimental** [clangd][]-based completer doesn't support this option. So it
  (and anything after this point) only applies to `libclang`-based completer.

If no [`.ycm_extra_conf.py`](#option-2-provide-the-flags-manually) is found,
YouCompleteMe automatically tries to load a compilation database if there is
one.

YCM looks for a file named `compile_commands.json` in the directory of the
opened file or in any directory above it in the hierarchy (recursively); when
the file is found, it is loaded.  YouCompleteMe performs the following lookups
when extracting flags for a particular file:

- If the database contains an entry for the file, the flags for that file are
  used.
- If the file is a header file and a source file with the same root exists in
  the database, the flags for the source file are used. For example, if the file
  is `/home/Test/project/src/lib/something.h` and the database contains an entry
  for `/home/Test/project/src/lib/something.cc`, then the flags for
  `/home/Test/project/src/lib/something.cc` are used.
- Otherwise, if any flags have been returned from the directory containing the
  requested file, those flags are used. This heuristic is intended to provide
  potentially working flags for newly created files.

Finally, YCM converts any relative paths in the extracted flags to absolute
paths. This ensures that compilation can be performed from any Vim working
directory.

#### Option 2: Provide the flags manually

_Note that this option doesn't work with **experimental** [clangd][]-based
completer. You can use a [compile_flags.txt][fixedcdb] file instead._

If you don't have a compilation database, or aren't able to generate one,
you have to tell YouCompleteMe how to compile your code some other way.

Every C-family project is different. It is not possible for YCM to guess what
compiler flags to supply for your project. Fortunately, YCM provides a mechanism
for you to generate the flags for a particular file with _arbitrary complexity_.
This is achieved by requiring you to provide a Python module which implements a
trivial function which, given the file name as argument, returns a list of
compiler flags to use to compile that file.

YCM looks for a `.ycm_extra_conf.py` file in the directory of the opened file or
in any directory above it in the hierarchy (recursively); when the file is
found, it is loaded (only once!) as a Python module. YCM calls a `Settings`
method in that module which should provide it with the information necessary to
compile the current file. You can also provide a path to a global configuration
file with the
[`g:ycm_global_ycm_extra_conf`](#the-gycm_global_ycm_extra_conf-option) option,
which will be used as a fallback. To prevent the execution of malicious code
from a file you didn't write YCM will ask you once per `.ycm_extra_conf.py` if
it is safe to load. This can be disabled and you can white-/blacklist files. See
the [`g:ycm_confirm_extra_conf`](#the-gycm_confirm_extra_conf-option) and
[`g:ycm_extra_conf_globlist`](#the-gycm_extra_conf_globlist-option) options
respectively.

This system was designed this way so that the user can perform any arbitrary
sequence of operations to produce a list of compilation flags YCM should hand
to Clang.

**NOTE**: It is highly recommended to include `-x <language>` flag to libclang.
This is so that the correct language is detected, particularly for header files.
Common values are `-x c` for C, `-x c++` for C++, `-x objc` for Objective-C, and
`-x cuda` for CUDA.

To give you an impression, if your C++ project is trivial, and your usual
compilation command is: `g++ -Wall -Wextra -Werror -o FILE.o FILE.cc`, then the
following `.ycm_extra_conf.py` is enough to get semantic analysis from
YouCompleteMe:

```python
def Settings( **kwargs ):
  return {
    'flags': [ '-x', 'c++', '-Wall', '-Wextra', '-Werror' ],
  }
```

As you can see from the trivial example, YCM calls the `Settings` method which
returns a dictionary with a single element `'flags'`. This element is a `list`
of compiler flags to pass to libclang for the current file. The absolute path of
that file is accessible under the `filename` key of the `kwargs` dictionary.
That's it! This is actually enough for most projects, but for complex projects
it is not uncommon to integrate directly with an existing build system using the
full power of the Python language.

For a more elaborate example,
[see ycmd's own `.ycm_extra_conf.py`][ycmd_flags_example]. You should be able to
use it _as a starting point_. **Don't** just copy/paste that file somewhere and
expect things to magically work; **your project needs different flags**. Hint:
just replace the strings in the `flags` variable with compilation flags
necessary for your project. That should be enough for 99% of projects.

You could also consider using [YCM-Generator][ygen] to generate the
`ycm_extra_conf.py` file.

#### Errors during compilation

If Clang encounters errors when compiling the header files that your file
includes, then it's probably going to take a long time to get completions.  When
the completion menu finally appears, it's going to have a large number of
unrelated completion strings (type/function names that are not actually
members). This is because Clang fails to build a precompiled preamble for your
file if there are any errors in the included headers and that preamble is key to
getting fast completions.

Call the `:YcmDiags` command to see if any errors or warnings were detected in
your file.


#### Selecting a C-family completion engine

Currently YCM supports two completion engines for C-family semantic completion.
One libclang-based and an **experimental** [clangd]-based completer. When in
doubt we recommend using the libclang-based engine. Here is a quick comparison
of the two completer engines:

-   **ycm_extra_conf.py**: Currently clangd does not support `ycm_extra_conf.py`
    therefore you must have a compilation database, whereas libclang can work
    with both.
-   **Project wide indexing**: Clangd has both dynamic and static index support.
    The dynamic index stores up-to-date symbols coming from any files you are
    currently editing, whereas static index contains project-wide symbol
    information. This symbol information is used for code completion and code
    navigation. Whereas libclang is limited to the current translation unit(TU).
-   **GoTo* **: Clangd provides all the GoTo requests libclang provides and it
    improves those using the above mentioned index information to contain
    project-wide information rather than just the current TU.
-   **Rename**: Clangd can perform semantic rename operations on the current
    file, whereas libclang doesn’t support such functionality.
-   **Code Completion**: Clangd can perform code completions at a lower latency
    than libclang; also, it has information about all the symbols in your
    project so it can suggest items outside your current TU and also provides
    proper `#include` insertions for those items.
-   **Format Code**: Clangd provides code formatting either for the selected
    lines or the whole file, whereas libclang doesn’t have such functionality.
-   **Performance**: Clangd has faster reparse and code completion times
    compared to libclang.

Note that for clangd to have some of the above mentioned functionality, you need
to provide a static index. For details on how to do that please have a look at
[clangd-indexing][].

To enable:

- libclang-based completer pass `--clang-completer`
- [clangd][]-based completer pass `--clangd-completer`

to `install.py` while following the [installation guide](#installation). As
mentioned before, pass `--clang-completer` when in doubt, since the
[clangd][]-based completer is still experimental.

### Java Semantic Completion

**NOTE**: Java support is currently experimental. Please let us know your
[feedback](#contact).

#### Java quick Start

1. Ensure that you have enabled the Java completer. See the
   [installation guide](#installation) for details.

2. Create a project file (gradle or maven) file in the root directory of your
   Java project, by following the instructions below.

3. If you previously used Eclim or Syntastic for Java, disable them for Java.

4. Edit a Java file from your project.

For the best experience, we highly recommend at least Vim 8.0.1493 when using
Java support with YouCompleteMe.

#### Java Project Files

In order to provide semantic analysis, the Java completion engine requires
knowledge of your project structure. In particular it needs to know the class
path to use, when compiling your code. Fortunately [jdt.ls][]
supports [eclipse project files][eclipse-project],
[maven projects][mvn-project] and [gradle projects][gradle-project].

**NOTE:** Our recommendation is to use either maven or gradle projects.

#### Diagnostic display - Syntastic

The native support for Java includes YCM's native realtime diagnostics display.
This can conflict with other diagnostics plugins like Syntastic, so when
enabling Java support, please **manually disable Syntastic Java diagnostics**.

Add the following to your `vimrc`:

```viml
let g:syntastic_java_checkers = []
```

#### Diagnostic display - Eclim

The native support for Java includes YCM's native realtime diagnostics display.
This can conflict with other diagnostics plugins like Eclim, so when enabling
Java support, please **manually disable Eclim Java diagnostics**.

Add the following to your `vimrc`:

```viml
let g:EclimFileTypeValidate = 0
```

**NOTE**: We recommend disabling Eclim entirely when editing Java with YCM's
native Java support. This can be done temporarily with `:EclimDisable`.

#### Eclipse Projects

Eclipse style projects require two files: [.project][eclipse-dot-project] and
[.classpath][eclipse-dot-classpath].

If your project already has these files due to previously being set up within
eclipse, then no setup is required. [jdt.ls][] should load the project just
fine (it's basically eclipse after all).

However, if not, it is possible (easy in fact) to craft them manually, though it
is not recommended. You're better off using gradle or maven (see below).

[A simple eclipse style project example][ycmd-eclipse-project] can be found in
the ycmd test directory. Normally all that is required is to copy these files to
the root of your project and to edit the `.classpath` to add additional
libraries, such as:

```xml
  <classpathentry kind="lib" path="/path/to/external/jar" />
  <classpathentry kind="lib" path="/path/to/external/java/source" />
```

It may also be necessary to change the directory in which your source files are
located (paths are relative to the .project file itself):

```xml
  <classpathentry kind="src" output="target/classes" path="path/to/src/" />
```

**NOTE**: The eclipse project and classpath files are not a public interface
and it is highly recommended to use Maven or Gradle project definitions if you
don't already use eclipse to manage your projects.

#### Maven Projects

Maven needs a file named [pom.xml][mvn-project] in the root of the project.
Once again a simple [pom.xml][ycmd-mvn-pom-xml] can be found in ycmd source.

The format of [pom.xml][mvn-project] files is way beyond the scope of this
document, but we do recommend using the various tools that can generate them for
you, if you're not familiar with them already.

#### Gradle Projects

Gradle projects require a [build.gradle][gradle-project]. Again, there is a
[trivial example in ycmd's tests][ycmd-gradle-project].

The format of [build.gradle][gradle-project] files is way beyond the scope of
this document, but we do recommend using the various tools that can generate
them for you, if you're not familiar with them already.

#### Troubleshooting

If you're not getting completions or diagnostics, check the server health:

* The Java completion engine takes a while to start up and parse your project.
  You should be able to see its progress in the command line, and
  `:YcmDebugInfo`. Ensure that the following lines are present:

```
--   jdt.ls Java Language Server running
--   jdt.ls Java Language Server Startup Status: Ready
```

* If the above lines don't appear after a few minutes, check the jdt.ls and ycmd
  log files using [`:YcmToggleLogs` ](#the-ycmtogglelogs-command). The jdt.ls
  log file is called `.log` (for some reason).

If you get a message about "classpath is incomplete", then make sure you have
correctly configured the [project files](#java-project-files).

If you get messages about unresolved imports, then make sure you have
correctly configured the [project files](#java-project-files), in particular
check that the classpath is set correctly.

For anything else, [contact us](#contact). Java support is experimental at
present so we'd love to hear your feedback! Please do remember to check
[CONTRIBUTING.md][contributing-md] for the list of diagnostics we'll need.

### Python Semantic Completion

YCM relies on the [Jedi][] engine to provide completion and code navigation. By
default, it will pick the version of Python running the [ycmd server][ycmd] and
use its `sys.path`. While this is fine for simple projects, this needs to be
configurable when working with virtual environments or in a project with
third-party packages. The next sections explain how to do that.

#### Working with virtual environments

A common practice when working on a Python project is to install its
dependencies in a virtual environment and develop the project inside that
environment. To support this, YCM needs to know the interpreter path of the
virtual environment. You can specify it by creating a `.ycm_extra_conf.py` file
at the root of your project with the following contents:

```python
def Settings( **kwargs ):
  return {
    'interpreter_path': '/path/to/virtual/environment/python'
  }
```

where `/path/to/virtual/environment/python` is the path to the Python used
by the virtual environment you are working in. Typically, the executable can be
found in the `Scripts` folder of the virtual environment directory on Windows
and in the `bin` folder on other platforms.

If you don't like having to create a `.ycm_extra_conf.py` file at the root of
your project and would prefer to specify the interpreter path with a Vim option,
read the [Configuring through Vim options](#configuring-through-vim-options)
section.

#### Working with third-party packages

Another common practice is to put the dependencies directly into the project and
add their paths to `sys.path` at runtime in order to import them. YCM needs to
be told about this path manipulation to support those dependencies. This can be
done by creating a `.ycm_extra_conf.py` file at the root of the project. This
file must define a `Settings( **kwargs )` function returning a dictionary with
the list of paths to prepend to `sys.path` under the `sys_path` key. For
instance, the following `.ycm_extra_conf.py`

```python
def Settings( **kwargs ):
  return {
    'sys_path': [
      '/path/to/some/third_party/package',
      '/path/to/another/third_party/package'
    ]
  }
```

adds the paths `/path/to/some/third_party/package` and
`/path/to/another/third_party/package` at the start of `sys.path`.

If you would rather prepend paths to `sys.path` with a Vim option, read the
[Configuring through Vim options](#configuring-through-vim-options) section.

If you need further control on how to add paths to `sys.path`, you should define
the `PythonSysPath( **kwargs )` function in the `.ycm_extra_conf.py` file. Its
keyword arguments are `sys_path` which contains the default `sys.path`, and
`interpreter_path` which is the path to the Python interpreter. Here's a trivial
example that insert the `/path/to/third_party/package` path at the second
position of `sys.path`:

```python
def PythonSysPath( **kwargs ):
  sys_path = kwargs[ 'sys_path' ]
  sys_path.insert( 1, '/path/to/third_party/package' )
  return sys_path
```

A more advanced example can be found in [YCM's own
`.ycm_extra_conf.py`][ycm_flags_example].

#### Configuring through Vim options

You may find inconvenient to have to create a `.ycm_extra_conf.py` file at the
root of each one of your projects in order to set the path to the Python
interpreter and/or add paths to `sys.path` and would prefer to be able to
configure those through Vim options. Don't worry, this is possible by using the
[`g:ycm_extra_conf_vim_data`](#the-gycm_extra_conf_vim_data-option) option and
creating a global extra configuration file. Let's take an example. Suppose that
you want to set the interpreter path with the `g:ycm_python_interpreter_path`
option and prepend paths to `sys.path` with the `g:ycm_python_sys_path` option.
Suppose also that you want to name the global extra configuration file
`global_extra_conf.py` and that you want to put it in your HOME folder. You
should then add the following lines to your vimrc:

```viml
let g:ycm_python_interpreter_path = ''
let g:ycm_python_sys_path = []
let g:ycm_extra_conf_vim_data = [
  \  'g:ycm_python_interpreter_path',
  \  'g:ycm_python_sys_path'
  \]
let g:ycm_global_ycm_extra_conf = '~/global_extra_conf.py'
```

and create the `~/global_extra_conf.py` file with the following contents:

```python
def Settings( **kwargs ):
  client_data = kwargs[ 'client_data' ]
  return {
    'interpreter_path': client_data[ 'g:ycm_python_interpreter_path' ],
    'sys_path': client_data[ 'g:ycm_python_sys_path' ]
  }
```

That's it. You are done. Note that you don't need to restart the server when
setting one of the options. YCM will automatically pick the new values.

### Rust Semantic Completion

Completions and GoTo commands within the current crate and its dependencies
should work out of the box with no additional configuration (provided that you
built YCM with the `--rust-completer` flag; see the [*Installation*
section](#installation) for details). For semantic analysis inclusive of the
standard library, you must have a local copy of [the Rust source
code][rust-src]. If using [rustup][], run the following command to download the
code:
```
rustup component add rust-src
```
YCM will find its location automatically. Otherwise, download the archive,
extract it somewhere, and set the following option so YCM can locate it:
```viml
" In this example, the Rust source code archive has been extracted to
" /usr/local/rust/rustc-1.20.0
let g:ycm_rust_src_path = '/usr/local/rust/rustc-1.20.0/src'
```

### JavaScript and TypeScript Semantic Completion

**NOTE:** YCM originally used the [Tern][] engine for JavaScript but due to
[Tern][] not being maintained anymore by its main author and the [TSServer][]
engine offering more features, YCM is moving to [TSServer][]. This won't affect
you if you were already using [Tern][] but you are encouraged to do the switch
by deleting the `third_party/ycmd/third_party/tern_runtime/node_modules`
directory in YCM folder. If you are a new user but still want to use [Tern][],
you should pass the `--js-completer` option to the `install.py` script during
installation. Further instructions on how to setup YCM with [Tern][] are
available on [the wiki][tern-instructions].

All JavaScript and TypeScript features are provided by the [TSServer][] engine,
which is included in the TypeScript SDK. To enable these features, install
[Node.js and npm][npm-install] and call the `install.py` script with the
`--ts-completer` flag.

[TSServer][] relies on [the `jsconfig.json` file][jsconfig.json] for JavaScript
and [the `tsconfig.json` file][tsconfig.json] for TypeScript to analyze your
project. Ensure the file exists at the root of your project.

To get diagnostics in JavaScript, set the `checkJs` option to `true` in your
`jsconfig.json` file:
```json
{
    "compilerOptions": {
        "checkJs": true
    }
}
```

### Semantic Completion for Other Languages

C-family, C#, Go, Java, Python, Rust, and JavaScript/TypeScript languages are
supported natively by YouCompleteMe using the [Clang][], [OmniSharp][],
[Gocode][]/[Godef][], [jdt.ls][], [Jedi][], [racer][], and [TSServer][] engines,
respectively. Check the [installation](#installation) section for instructions
to enable these features if desired.

YCM will use your `omnifunc` (see `:h omnifunc` in Vim) as a source for semantic
completions if it does not have a native semantic completion engine for your
file's filetype. Vim comes with okayish omnifuncs for various languages like
Ruby, PHP, etc. It depends on the language.

You can get a stellar omnifunc for Ruby with [Eclim][]. Just make sure you have
the _latest_ Eclim installed and configured (this means Eclim `>= 2.2.*` and
Eclipse `>= 4.2.*`).

After installing Eclim remember to create a new Eclipse project within your
application by typing `:ProjectCreate <path-to-your-project> -n ruby` inside vim
and don't forget to have `let g:EclimCompletionMethod = 'omnifunc'` in your
vimrc. This will make YCM and Eclim play nice; YCM will use Eclim's omnifuncs as
the data source for semantic completions and provide the auto-triggering and
subsequence-based matching (and other YCM features) on top of it.

### Writing New Semantic Completers

You have two options here: writing an `omnifunc` for Vim's omnicomplete system
that YCM will then use through its omni-completer, or a custom completer for YCM
using the [Completer API][completer-api].

Here are the differences between the two approaches:

- You have to use VimScript to write the omnifunc, but get to use Python to
  write for the Completer API; this by itself should make you want to use the
  API.
- The Completer API is a _much_ more powerful way to integrate with YCM and it
  provides a wider set of features. For instance, you can make your Completer
  query your semantic back-end in an asynchronous fashion, thus not blocking
  Vim's GUI thread while your completion system is processing stuff. This is
  impossible with VimScript. All of YCM's completers use the Completer API.
- Performance with the Completer API is better since Python executes faster than
  VimScript.

If you want to use the `omnifunc` system, see the relevant Vim docs with `:h
complete-functions`. For the Completer API, see [the API docs][completer-api].

If you want to upstream your completer into YCM's source, you should use the
Completer API.

### Diagnostic Display

YCM will display diagnostic notifications for the C-family, C#, Java,
JavaScript, and TypeScript languages. Since YCM continuously recompiles your
file as you type, you'll get notified of errors and warnings in your file as
fast as possible.

Here are the various pieces of the diagnostic UI:

- Icons show up in the Vim gutter on lines that have a diagnostic.
- Regions of text related to diagnostics are highlighted (by default, a red
  wavy underline in `gvim` and a red background in `vim`).
- Moving the cursor to a line with a diagnostic echoes the diagnostic text.
- Vim's location list is automatically populated with diagnostic data (off by
  default, see options).

The new diagnostics (if any) will be displayed the next time you press any key
on the keyboard. So if you stop typing and just wait for the new diagnostics to
come in, that _will not work_. You need to press some key for the GUI to update.

Having to press a key to get the updates is unfortunate, but cannot be changed
due to the way Vim internals operate; there is no way that a background task can
update Vim's GUI after it has finished running.  You _have to_ press a key. This
will make YCM check for any pending diagnostics updates.

You _can_ force a full, blocking compilation cycle with the
`:YcmForceCompileAndDiagnostics` command (you may want to map that command to a
key; try putting `nnoremap <F5> :YcmForceCompileAndDiagnostics<CR>` in your
vimrc). Calling this command will force YCM to immediately recompile your file
and display any new diagnostics it encounters. Do note that recompilation with
this command may take a while and during this time the Vim GUI _will_ be
blocked.

YCM will display a short diagnostic message when you move your cursor to the
line with the error. You can get a detailed diagnostic message with the
`<leader>d` key mapping (can be changed in the options) YCM provides when your
cursor is on the line with the diagnostic.

You can also see the full diagnostic message for all the diagnostics in the
current file in Vim's `locationlist`, which can be opened with the `:lopen` and
`:lclose` commands (make sure you have set `let
g:ycm_always_populate_location_list = 1` in your vimrc). A good way to toggle
the display of the `locationlist` with a single key mapping is provided by
another (very small) Vim plugin called [ListToggle][] (which also makes it
possible to change the height of the `locationlist` window), also written by
yours truly.

#### Diagnostic Highlighting Groups

You can change the styling for the highlighting groups YCM uses. For the signs
in the Vim gutter, the relevant groups are:

- `YcmErrorSign`, which falls back to group `SyntasticErrorSign` and then
  `error` if they exist
- `YcmWarningSign`, which falls back to group `SyntasticWarningSign` and then
  `todo` if they exist

You can also style the line that has the warning/error with these groups:

- `YcmErrorLine`, which falls back to group `SyntasticErrorLine` if it exists
- `YcmWarningLine`, which falls back to group `SyntasticWarningLine` if it
  exists

Note that the line highlighting groups only work when the
[`g:ycm_enable_diagnostic_signs`](#the-gycm_enable_diagnostic_signs-option)
option is set. If you want highlighted lines but no signs in the Vim gutter,
ensure that your Vim version is 7.4.2201 or later and set the `signcolumn`
option to `off` in your vimrc:

```viml
set signcolumn=off
```

The syntax groups used to highlight regions of text with errors/warnings:
- `YcmErrorSection`, which falls back to group `SyntasticError` if it exists and
  then `SpellBad`
- `YcmWarningSection`, which falls back to group `SyntasticWarning` if it exists
  and then `SpellCap`

Here's how you'd change the style for a group:

```viml
highlight YcmErrorLine guibg=#3f0000
```

Commands
--------

### The `:YcmRestartServer` command

If the [ycmd completion server][ycmd] suddenly stops for some reason, you can
restart it with this command.

### The `:YcmForceCompileAndDiagnostics` command

Calling this command will force YCM to immediately recompile your file
and display any new diagnostics it encounters. Do note that recompilation with
this command may take a while and during this time the Vim GUI _will_ be
blocked.

You may want to map this command to a key; try putting `nnoremap <F5>
:YcmForceCompileAndDiagnostics<CR>` in your vimrc.

### The `:YcmDiags` command

Calling this command will fill Vim's `locationlist` with errors or warnings if
any were detected in your file and then open it. If a given error or warning can
be fixed by a call to `:YcmCompleter FixIt`, then ` (FixIt available)` is
appended to the error or warning text. See the `FixIt` completer subcommand for
more information.

**NOTE:** The absence of ` (FixIt available)` does not strictly imply a fix-it
is not available as not all completers are able to provide this indication. For
example, the c-sharp completer provides many fix-its but does not add this
additional indication.

The `g:ycm_open_loclist_on_ycm_diags` option can be used to prevent the location
list from opening, but still have it filled with new diagnostic data. See the
_Options_ section for details.

### The `:YcmShowDetailedDiagnostic` command

This command shows the full diagnostic text when the user's cursor is on the
line with the diagnostic.

### The `:YcmDebugInfo` command

This will print out various debug information for the current file. Useful to
see what compile commands will be used for the file if you're using the semantic
completion engine.

### The `:YcmToggleLogs` command

This command presents the list of logfiles created by YCM, the [ycmd
server][ycmd], and the semantic engine server for the current filetype, if any.
One of these logfiles can be opened in the editor (or closed if already open) by
entering the corresponding number or by clicking on it with the mouse.
Additionally, this command can take the logfile names as arguments. Use the
`<TAB>` key (or any other key defined by the `wildchar` option) to complete the
arguments or to cycle through them (depending on the value of the `wildmode`
option). Each logfile given as an argument is directly opened (or closed if
already open) in the editor. Only for debugging purposes.

### The `:YcmCompleter` command

This command gives access to a number of additional [IDE-like
features](#quick-feature-summary) in YCM, for things like semantic GoTo, type
information, FixIt and refactoring.

This command accepts a range that can either be specified through a selection in
one of Vim's visual modes (see `:h visual-use`) or on the command line. For
instance, `:2,5YcmCompleter` will apply the command from line 2 to line 5. This
is useful for [the `Format` subcommand](#the-format-subcommand).

Call `YcmCompleter` without further arguments for a list of the commands you can
call for the current completer.

See the [file type feature summary](#quick-feature-summary) for an overview of
the features available for each file type. See the _YcmCompleter subcommands_
section for more information on the available subcommands and their usage.

YcmCompleter Subcommands
------------------------

**NOTE:** See the docs for the `YcmCompleter` command before tackling this
section.

The invoked subcommand is automatically routed to the currently active semantic
completer, so `:YcmCompleter GoToDefinition` will invoke the `GoToDefinition`
subcommand on the Python semantic completer if the currently active file is a
Python one and on the Clang completer if the currently active file is a C-family
language one.

You may also want to map the subcommands to something less verbose; for
instance, `nnoremap <leader>jd :YcmCompleter GoTo<CR>`
maps the `<leader>jd` sequence to the longer subcommand invocation.

### GoTo Commands

These commands are useful for jumping around and exploring code. When moving
the cursor, the subcommands add entries to Vim's `jumplist` so you can use
`CTRL-O` to jump back to where you were before invoking the command (and
`CTRL-I` to jump forward; see `:h jumplist` for details). If there is more
than one destination, the quickfix list (see `:h quickfix`) is populated with
the available locations and opened to full width at the bottom of the screen.
You can change this behavior by using [the `YcmQuickFixOpened`
autocommand](#the-ycmquickfixopened-autocommand).

#### The `GoToInclude` subcommand

Looks up the current line for a header and jumps to it.

Supported in filetypes: `c, cpp, objc, objcpp, cuda`

#### The `GoToDeclaration` subcommand

Looks up the symbol under the cursor and jumps to its declaration.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, go, java, javascript,
python, rust, typescript`

#### The `GoToDefinition` subcommand

Looks up the symbol under the cursor and jumps to its definition.

**NOTE:** For C-family languages **this only works in certain situations**,
namely when the definition of the symbol is in the current translation unit. A
translation unit consists of the file you are editing and all the files you are
including with `#include` directives (directly or indirectly) in that file.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, go, java, javascript,
python, rust, typescript`

#### The `GoTo` subcommand

This command tries to perform the "most sensible" GoTo operation it can.
Currently, this means that it tries to look up the symbol under the cursor and
jumps to its definition if possible; if the definition is not accessible from
the current translation unit, jumps to the symbol's declaration. For
C-family languages, it first tries to look up the current line for a header and
jump to it. For C#, implementations are also considered and preferred.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, go, java, javascript,
python, rust, typescript`

#### The `GoToImprecise` subcommand

WARNING: This command trades correctness for speed!

Same as the `GoTo` command except that it doesn't recompile the file with
libclang before looking up nodes in the AST. This can be very useful when you're
editing files that take long to compile but you know that you haven't made any
changes since the last parse that would lead to incorrect jumps. When you're
just browsing around your codebase, this command can spare you quite a bit of
latency.

Supported in filetypes: `c, cpp, objc, objcpp, cuda`

#### The `GoToReferences` subcommand

This command attempts to find all of the references within the project to the
identifier under the cursor and populates the quickfix list with those
locations.

Supported in filetypes: `java, javascript, python, typescript`

#### The `GoToImplementation` subcommand

Looks up the symbol under the cursor and jumps to its implementation (i.e.
non-interface). If there are multiple implementations, instead provides a list
of implementations to choose from.

Supported in filetypes: `cs`

#### The `GoToImplementationElseDeclaration` subcommand

Looks up the symbol under the cursor and jumps to its implementation if one,
else jump to its declaration. If there are multiple implementations, instead
provides a list of implementations to choose from.

Supported in filetypes: `cs`

#### The `GoToType` subcommand

Looks up the symbol under the cursor and jumps to the definition of its type
e.g. if the symbol is an object, go to the definition of its class.

Supported in filetypes: `javascript, typescript`

### Semantic Information Commands

These commands are useful for finding static information about the code, such
as the types of variables, viewing declarations and documentation strings.

#### The `GetType` subcommand

Echos the type of the variable or method under the cursor, and where it differs,
the derived type.

For example:

```c++
    std::string s;
```

Invoking this command on `s` returns `std::string => std::basic_string<char>`

**NOTE:** Causes re-parsing of the current translation unit.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, java, javascript,
python, typescript`

#### The `GetTypeImprecise` subcommand

WARNING: This command trades correctness for speed!

Same as the `GetType` command except that it doesn't recompile the file with
libclang before looking up nodes in the AST. This can be very useful when you're
editing files that take long to compile but you know that you haven't made any
changes since the last parse that would lead to incorrect type. When you're
just browsing around your codebase, this command can spare you quite a bit of
latency.

Supported in filetypes: `c, cpp, objc, objcpp, cuda`

#### The `GetParent` subcommand

Echos the semantic parent of the point under the cursor.

The semantic parent is the item that semantically contains the given position.

For example:

```c++
class C {
    void f();
};

void C::f() {

}
```

In the out-of-line definition of `C::f`, the semantic parent is the class `C`,
of which this function is a member.

In the example above, both declarations of `C::f` have `C` as their semantic
context, while the lexical context of the first `C::f` is `C` and the lexical
context of the second `C::f` is the translation unit.

For global declarations, the semantic parent is the translation unit.

**NOTE:** Causes re-parsing of the current translation unit.

Supported in filetypes: `c, cpp, objc, objcpp, cuda`

#### The `GetDoc` subcommand

Displays the preview window populated with quick info about the identifier
under the cursor. Depending on the file type, this includes things like:

* The type or declaration of identifier,
* Doxygen/javadoc comments,
* Python docstrings,
* etc.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, java, javascript,
python, typescript, rust`

#### The `GetDocImprecise` subcommand

WARNING: This command trades correctness for speed!

Same as the `GetDoc` command except that it doesn't recompile the file with
libclang before looking up nodes in the AST. This can be very useful when you're
editing files that take long to compile but you know that you haven't made any
changes since the last parse that would lead to incorrect docs. When you're
just browsing around your codebase, this command can spare you quite a bit of
latency.

Supported in filetypes: `c, cpp, objc, objcpp, cuda`

### Refactoring Commands

These commands make changes to your source code in order to perform refactoring
or code correction. YouCompleteMe does not perform any action which cannot be
undone, and never saves or writes files to the disk.

#### The `FixIt` subcommand

Where available, attempts to make changes to the buffer to correct diagnostics
on the current line. Where multiple suggestions are available (such as when
there are multiple ways to resolve a given warning, or where multiple
diagnostics are reported for the current line), the options are presented
and one can be selected.

Completers which provide diagnostics may also provide trivial modifications to
the source in order to correct the diagnostic. Examples include syntax errors
such as missing trailing semi-colons, spurious characters, or other errors which
the semantic engine can deterministically suggest corrections.

If no fix-it is available for the current line, or there is no diagnostic on the
current line, this command has no effect on the current buffer. If any
modifications are made, the number of changes made to the buffer is echo'd and
the user may use the editor's undo command to revert.

When a diagnostic is available, and `g:ycm_echo_current_diagnostic` is set to 1,
then the text ` (FixIt)` is appended to the echo'd diagnostic when the
completer is able to add this indication. The text ` (FixIt available)` is
also appended to the diagnostic text in the output of the `:YcmDiags` command
for any diagnostics with available fix-its (where the completer can provide this
indication).

**NOTE:** Causes re-parsing of the current translation unit.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, java, javascript,
typescript`

#### The `RefactorRename <new name>` subcommand

In supported file types, this command attempts to perform a semantic rename of
the identifier under the cursor. This includes renaming declarations,
definitions and usages of the identifier, or any other language-appropriate
action. The specific behavior is defined by the semantic engine in use.

Similar to `FixIt`, this command applies automatic modifications to your source
files. Rename operations may involve changes to multiple files, which may or may
not be open in Vim buffers at the time. YouCompleteMe handles all of this for
you. The behavior is described in [the following section](#multi-file-refactor).

Supported in filetypes: `java, javascript, typescript`

#### Multi-file Refactor

When a Refactor or FixIt command touches multiple files, YouCompleteMe attempts
to apply those modifications to any existing open, visible buffer in the current
tab. If no such buffer can be found, YouCompleteMe opens the file in a new
small horizontal split at the top of the current window, applies the change,
and then *hides* the window. **NOTE:** The buffer remains open, and must be
manually saved. A confirmation dialog is opened prior to doing this to remind
you that this is about to happen.

Once the modifications have been made, the quickfix list (see `:help quickfix`)
is populated with the locations of all modifications. This can be used to review
all automatic changes made by using `:copen`. Typically, use the `CTRL-W
<enter>` combination to open the selected file in a new split. It is possible to
customize how the quickfix window is opened by using [the `YcmQuickFixOpened`
autocommand](#the-ycmquickfixopened-autocommand).

The buffers are *not* saved automatically. That is, you must save the modified
buffers manually after reviewing the changes from the quickfix list. Changes
can be undone using Vim's powerful undo features (see `:help undo`). Note
that Vim's undo is per-buffer, so to undo all changes, the undo commands must
be applied in each modified buffer separately.

**NOTE:** While applying modifications, Vim may find files which are already
open and have a swap file. The command is aborted if you select Abort or Quit in
any such prompts. This leaves the Refactor operation partially complete and must
be manually corrected using Vim's undo features. The quickfix list is *not*
populated in this case. Inspect `:buffers` or equivalent (see `:help buffers`)
to see the buffers that were opened by the command.

#### The `Format` subcommand

This command formats the whole buffer or some part of it according to the value
of the Vim options `shiftwidth` and `expandtab` (see `:h 'sw'` and `:h et`
respectively). To format a specific part of your document, you can either select
it in one of Vim's visual modes (see `:h visual-use`) and run the command or
directly enter the range on the command line, e.g. `:2,5YcmCompleter Format` to
format it from line 2 to line 5.

Supported in filetypes: `java, javascript, typescript`

#### The `OrganizeImports` subcommand

This command removes unused imports and sorts imports in the current file. It
can also group imports from the same module in TypeScript and resolves imports
in Java.

Supported in filetypes: `java, javascript, typescript`

### Miscellaneous Commands

These commands are for general administration, rather than IDE-like features.
They cover things like the semantic engine server instance and compilation
flags.

#### The `RestartServer` subcommand

Restarts the semantic-engine-as-localhost-server for those semantic engines that
work as separate servers that YCM talks to.

Supported in filetypes: `cs, go, java, javascript, rust, typescript`

#### The `ClearCompilationFlagCache` subcommand

YCM caches the flags it gets from the `Settings` function in your
`.ycm_extra_conf.py` file unless you return them with the `do_cache` parameter
set to `False`. It also caches the flags extracted from the compilation
database. The cache is in memory and is never invalidated (unless you restart
the server with the `:YcmRestartServer` command).

This command clears that cache entirely. YCM will then re-query your
`Settings` function or your compilation database as needed in the future.

Supported in filetypes: `c, cpp, objc, objcpp, cuda`

#### The `ReloadSolution` subcommand

Instruct the Omnisharp server to clear its cache and reload all files from disk.
This is useful when files are added, removed, or renamed in the solution, files
are changed outside of Vim, or whenever Omnisharp cache is out-of-sync.

Supported in filetypes: `cs`

Functions
--------

### The `youcompleteme#GetErrorCount` function

Get the number of YCM Diagnostic errors. If no errors are present, this function
returns 0.

For example:
```viml
  call youcompleteme#GetErrorCount()
```

Both this function and `youcompleteme#GetWarningCount` can be useful when
integrating YCM with other Vim plugins. For example, a [lightline][] user could
add a diagnostics section to their statusline which would display the number of
errors and warnings.

### The `youcompleteme#GetWarningCount` function

Get the number of YCM Diagnostic warnings. If no warnings are present, this
function returns 0.

For example:
```viml
  call youcompleteme#GetWarningCount()
```

Autocommands
------------

### The `YcmLocationOpened` autocommand

This `User` autocommand is fired when YCM opens the location list window in
response to the `YcmDiags` command. By default, the location list window is
opened to the bottom of the current window and its height is set to fit all
entries. This behavior can be overridden by using the `YcmLocationOpened`
autocommand which is triggered while the cursor is in the location list window.
For instance:
```viml
function! s:CustomizeYcmLocationWindow()
  " Move the window to the top of the screen.
  wincmd K
  " Set the window height to 5.
  5wincmd _
  " Switch back to working window.
  wincmd p
endfunction

autocmd User YcmLocationOpened call s:CustomizeYcmLocationWindow()
```

### The `YcmQuickFixOpened` autocommand

This `User` autocommand is fired when YCM opens the quickfix window in response
to the `GoTo*` and `RefactorRename` subcommands. By default, the quickfix window
is opened to full width at the bottom of the screen and its height is set to fit
all entries. This behavior can be overridden by using the `YcmQuickFixOpened`
autocommand which is triggered while the cursor is in the quickfix window. For
instance:
```viml
function! s:CustomizeYcmQuickFixWindow()
  " Move the window to the top of the screen.
  wincmd K
  " Set the window height to 5.
  5wincmd _
endfunction

autocmd User YcmQuickFixOpened call s:CustomizeYcmQuickFixWindow()
```

Options
-------

All options have reasonable defaults so if the plug-in works after installation
you don't need to change any options. These options can be configured in your
[vimrc script][vimrc] by including a line like this:

```viml
let g:ycm_min_num_of_chars_for_completion = 1
```

Note that after changing an option in your [vimrc script][vimrc] you have to
restart [ycmd][] with the `:YcmRestartServer` command for the changes to take
effect.

### The `g:ycm_min_num_of_chars_for_completion` option

This option controls the number of characters the user needs to type before
identifier-based completion suggestions are triggered. For example, if the
option is set to `2`, then when the user types a second alphanumeric character
after a whitespace character, completion suggestions will be triggered. This
option is NOT used for semantic completion.

Setting this option to a high number like `99` effectively turns off the
identifier completion engine and just leaves the semantic engine.

Default: `2`

```viml
let g:ycm_min_num_of_chars_for_completion = 2
```

### The `g:ycm_min_num_identifier_candidate_chars` option

This option controls the minimum number of characters that a completion
candidate coming from the identifier completer must have to be shown in the
popup menu.

A special value of `0` means there is no limit.

**NOTE:** This option only applies to the identifier completer; it has no effect
on the various semantic completers.

Default: `0`

```viml
let g:ycm_min_num_identifier_candidate_chars = 0
```

### The `g:ycm_max_num_candidates` option

This option controls the maximum number of semantic completion suggestions shown
in the completion menu. This only applies to suggestions from semantic
completion engines; see [the `g:ycm_max_identifier_candidates`
option](#the-gycm_max_num_identifier_candidates-option) to limit the number of
suggestions from the identifier-based engine.

A special value of `0` means there is no limit.

**NOTE:** Setting this option to `0` or to a value greater than `100` is not
recommended as it will slow down completion when there are a very large number
of suggestions.

Default: `50`

```viml
let g:ycm_max_num_candidates = 50
```

### The `g:ycm_max_num_identifier_candidates` option

This option controls the maximum number of completion suggestions from the
identifier-based engine shown in the completion menu.

A special value of `0` means there is no limit.

**NOTE:** Setting this option to `0` or to a value greater than `100` is not
recommended as it will slow down completion when there are a very large number
of suggestions.

Default: `10`

```viml
let g:ycm_max_num_identifier_candidates = 10
```

### The `g:ycm_auto_trigger` option

When set to `0`, this option turns off YCM's identifier completer (the
as-you-type popup) _and_ the semantic triggers (the popup you'd get after typing
`.` or `->` in say C++). You can still force semantic completion with the
`<C-Space>` shortcut.

If you want to just turn off the identifier completer but keep the semantic
triggers, you should set `g:ycm_min_num_of_chars_for_completion` to a high
number like `99`.

Default: `1`

```viml
let g:ycm_auto_trigger = 1
```

### The `g:ycm_filetype_whitelist` option

This option controls for which Vim filetypes (see `:h filetype`) should YCM be
turned on. The option value should be a Vim dictionary with keys being filetype
strings (like `python`, `cpp`, etc.) and values being unimportant (the
dictionary is used like a hash set, meaning that only the keys matter).

The `*` key is special and matches all filetypes. By default, the whitelist
contains only this `*` key.

YCM also has a `g:ycm_filetype_blacklist` option that lists filetypes for which
YCM shouldn't be turned on. YCM will work only in filetypes that both the
whitelist and the blacklist allow (the blacklist "allows" a filetype by _not_
having it as a key).

For example, let's assume you want YCM to work in files with the `cpp` filetype.
The filetype should then be present in the whitelist either directly (`cpp` key
in the whitelist) or indirectly through the special `*` key. It should _not_ be
present in the blacklist.

Filetypes that are blocked by the either of the lists will be completely ignored
by YCM, meaning that neither the identifier-based completion engine nor the
semantic engine will operate in them.

You can get the filetype of the current file in Vim with `:set ft?`.

Default: `{'*': 1}`

```viml
let g:ycm_filetype_whitelist = {'*': 1}
```

### The `g:ycm_filetype_blacklist` option

This option controls for which Vim filetypes (see `:h filetype`) should YCM be
turned off. The option value should be a Vim dictionary with keys being filetype
strings (like `python`, `cpp`, etc.) and values being unimportant (the
dictionary is used like a hash set, meaning that only the keys matter).

See the `g:ycm_filetype_whitelist` option for more details on how this works.

Default: `[see next line]`

```viml
let g:ycm_filetype_blacklist = {
      \ 'tagbar': 1,
      \ 'notes': 1,
      \ 'markdown': 1,
      \ 'netrw': 1,
      \ 'unite': 1,
      \ 'text': 1,
      \ 'vimwiki': 1,
      \ 'pandoc': 1,
      \ 'infolog': 1,
      \ 'mail': 1
      \}
```

### The `g:ycm_filetype_specific_completion_to_disable` option

This option controls for which Vim filetypes (see `:h filetype`) should the YCM
semantic completion engine be turned off. The option value should be a Vim
dictionary with keys being filetype strings (like `python`, `cpp`, etc.) and
values being unimportant (the dictionary is used like a hash set, meaning that
only the keys matter). The listed filetypes will be ignored by the YCM semantic
completion engine, but the identifier-based completion engine will still trigger
in files of those filetypes.

Note that even if semantic completion is not turned off for a specific filetype,
you will not get semantic completion if the semantic engine does not support
that filetype.

You can get the filetype of the current file in Vim with `:set ft?`.

Default: `[see next line]`

```viml
let g:ycm_filetype_specific_completion_to_disable = {
      \ 'gitcommit': 1
      \}
```

### The `g:ycm_filepath_blacklist` option

This option controls for which Vim filetypes (see `:h filetype`) should filepath
completion be disabled. The option value should be a Vim dictionary with keys
being filetype strings (like `python`, `cpp`, etc.) and values being unimportant
(the dictionary is used like a hash set, meaning that only the keys matter).

The `*` key is special and matches all filetypes. Use this key if you want to
completely disable filepath completion:
```viml
let g:ycm_filepath_blacklist = {'*': 1}
```

You can get the filetype of the current file in Vim with `:set ft?`.

Default: `[see next line]`

```viml
let g:ycm_filepath_blacklist = {
      \ 'html': 1,
      \ 'jsx': 1,
      \ 'xml': 1,
      \}
```

### The `g:ycm_show_diagnostics_ui` option

When set, this option turns on YCM's diagnostic display features. See the
_Diagnostic display_ section in the _User Manual_ for more details.

Specific parts of the diagnostics UI (like the gutter signs, text highlighting,
diagnostic echo and auto location list population) can be individually turned on
or off. See the other options below for details.

Note that YCM's diagnostics UI is only supported for C-family languages.

When set, this option also makes YCM remove all Syntastic checkers set for the
`c`, `cpp`, `objc`, `objcpp`, and `cuda` filetypes since this would conflict
with YCM's own diagnostics UI.

If you're using YCM's identifier completer in C-family languages but cannot use
the clang-based semantic completer for those languages _and_ want to use the GCC
Syntastic checkers, unset this option.

Default: `1`

```viml
let g:ycm_show_diagnostics_ui = 1
```

### The `g:ycm_error_symbol` option

YCM will use the value of this option as the symbol for errors in the Vim
gutter.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the `g:syntastic_error_symbol` option
before using this option's default.

Default: `>>`

```viml
let g:ycm_error_symbol = '>>'
```

### The `g:ycm_warning_symbol` option

YCM will use the value of this option as the symbol for warnings in the Vim
gutter.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the `g:syntastic_warning_symbol` option
before using this option's default.

Default: `>>`

```viml
let g:ycm_warning_symbol = '>>'
```

### The `g:ycm_enable_diagnostic_signs` option

When this option is set, YCM will put icons in Vim's gutter on lines that have a
diagnostic set. Turning this off will also turn off the `YcmErrorLine` and
`YcmWarningLine` highlighting.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the `g:syntastic_enable_signs` option
before using this option's default.

Default: `1`

```viml
let g:ycm_enable_diagnostic_signs = 1
```

### The `g:ycm_enable_diagnostic_highlighting` option

When this option is set, YCM will highlight regions of text that are related to
the diagnostic that is present on a line, if any.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the `g:syntastic_enable_highlighting`
option before using this option's default.

Default: `1`

```viml
let g:ycm_enable_diagnostic_highlighting = 1
```

### The `g:ycm_echo_current_diagnostic` option

When this option is set, YCM will echo the text of the diagnostic present on the
current line when you move your cursor to that line. If a `FixIt` is available
for the current diagnostic, then ` (FixIt)` is appended.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the `g:syntastic_echo_current_error`
option before using this option's default.

Default: `1`

```viml
let g:ycm_echo_current_diagnostic = 1
```

### The `g:ycm_filter_diagnostics` option

This option controls which diagnostics will be rendered by YCM. This option
holds a dictionary of key-values, where the keys are Vim's filetype strings
delimited by commas and values are dictionaries describing the filter.

A filter is a dictionary of key-values, where the keys are the type of filter,
and the value is a list of arguments to that filter. In the case of just a
single item in the list, you may omit the brackets and just provide the argument
directly. If any filter matches a diagnostic, it will be dropped and YCM will
not render it.

The following filter types are supported:

- "regex": Accepts a string [regular expression][python-re]. This type matches
when the regex (treated as case-insensitive) is found in the diagnostic text.
- "level": Accepts a string level, either "warning" or "error." This type
matches when the diagnostic has the same level.

**NOTE:** The regex syntax is **NOT** Vim's, it's [Python's][python-re].

Default: `{}`

```viml
let g:ycm_filter_diagnostics = {
  \ "java": {
  \      "regex": [ ".*taco.*", ... ],
  \      "level": "error",
  \      ...
  \    }
  \ }
```

### The `g:ycm_always_populate_location_list` option

When this option is set, YCM will populate the location list automatically every
time it gets new diagnostic data. This option is off by default so as not to
interfere with other data you might have placed in the location list.

See `:help location-list` in Vim to learn more about the location list.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the
`g:syntastic_always_populate_loc_list` option before using this option's
default.

Default: `0`

```viml
let g:ycm_always_populate_location_list = 0
```

### The `g:ycm_open_loclist_on_ycm_diags` option

When this option is set, `:YcmDiags` will automatically open the location list
after forcing a compilation and filling the list with diagnostic data.

See `:help location-list` in Vim to learn more about the location list.

Default: `1`

```viml
let g:ycm_open_loclist_on_ycm_diags = 1
```

### The `g:ycm_complete_in_comments` option

When this option is set to `1`, YCM will show the completion menu even when
typing inside comments.

Default: `0`

```viml
let g:ycm_complete_in_comments = 0
```

### The `g:ycm_complete_in_strings` option

When this option is set to `1`, YCM will show the completion menu even when
typing inside strings.

Note that this is turned on by default so that you can use the filename
completion inside strings. This is very useful for instance in C-family files
where typing `#include "` will trigger the start of filename completion. If you
turn off this option, you will turn off filename completion in such situations
as well.

Default: `1`

```viml
let g:ycm_complete_in_strings = 1
```

### The `g:ycm_collect_identifiers_from_comments_and_strings` option

When this option is set to `1`, YCM's identifier completer will also collect
identifiers from strings and comments. Otherwise, the text in comments and
strings will be ignored.

Default: `0`

```viml
let g:ycm_collect_identifiers_from_comments_and_strings = 0
```

### The `g:ycm_collect_identifiers_from_tags_files` option

When this option is set to `1`, YCM's identifier completer will also collect
identifiers from tags files. The list of tags files to examine is retrieved from
the `tagfiles()` Vim function which examines the `tags` Vim option. See `:h
'tags'` for details.

YCM will re-index your tags files if it detects that they have been modified.

The only supported tag format is the [Exuberant Ctags format][ctags-format]. The
format from "plain" ctags is NOT supported. Ctags needs to be called with the
`--fields=+l` option (that's a lowercase `L`, not a one) because YCM needs the
`language:<lang>` field in the tags output.

See the _FAQ_ for pointers if YCM does not appear to read your tag files.

This option is off by default because it makes Vim slower if your tags are on a
network directory.

Default: `0`

```viml
let g:ycm_collect_identifiers_from_tags_files = 0
```

### The `g:ycm_seed_identifiers_with_syntax` option

When this option is set to `1`, YCM's identifier completer will seed its
identifier database with the keywords of the programming language you're
writing.

Since the keywords are extracted from the Vim syntax file for the filetype, all
keywords may not be collected, depending on how the syntax file was written.
Usually at least 95% of the keywords are successfully extracted.

Default: `0`

```viml
let g:ycm_seed_identifiers_with_syntax = 0
```

### The `g:ycm_extra_conf_vim_data` option

If you're using semantic completion for C-family files, this option might come
handy; it's a way of sending data from Vim to your `Settings` function in
your `.ycm_extra_conf.py` file.

This option is supposed to be a list of VimScript expression strings that are
evaluated for every request to the [ycmd server][ycmd] and then passed to your
`Settings` function as a `client_data` keyword argument.

For instance, if you set this option to `['v:version']`, your `Settings`
function will be called like this:

```python
# The '801' value is of course contingent on Vim 8.1; in 8.0 it would be '800'
Settings( ..., client_data = { 'v:version': 801 } )
```

So the `client_data` parameter is a dictionary mapping Vim expression strings to
their values at the time of the request.

The correct way to define parameters for your `Settings` function:

```python
def Settings( **kwargs ):
```

You can then get to `client_data` with `kwargs['client_data']`.

Default: `[]`

```viml
let g:ycm_extra_conf_vim_data = []
```

### The `g:ycm_server_python_interpreter` option

YCM will by default search for an appropriate Python interpreter on your system.
You can use this option to override that behavior and force the use of a
specific interpreter of your choosing.

**NOTE:** This interpreter is only used for the [ycmd server][ycmd]. The YCM
client running inside Vim always uses the Python interpreter that's embedded
inside Vim.

Default: `''`

```viml
let g:ycm_server_python_interpreter = ''
```

### The `g:ycm_keep_logfiles` option

When this option is set to `1`, YCM and the [ycmd completion server][ycmd] will
keep the logfiles around after shutting down (they are deleted on shutdown by
default).

To see where the logfiles are, call `:YcmDebugInfo`.

Default: `0`

```viml
let g:ycm_keep_logfiles = 0
```

### The `g:ycm_log_level` option

The logging level that YCM and the [ycmd completion server][ycmd] use. Valid
values are the following, from most verbose to least verbose:
- `debug`
- `info`
- `warning`
- `error`
- `critical`

Note that `debug` is _very_ verbose.

Default: `info`

```viml
let g:ycm_log_level = 'info'
```

### The `g:ycm_auto_start_csharp_server` option

When set to `1`, the OmniSharp server will be automatically started (once per
Vim session) when you open a C# file.

Default: `1`

```viml
let g:ycm_auto_start_csharp_server = 1
```

### The `g:ycm_auto_stop_csharp_server` option

When set to `1`, the OmniSharp server will be automatically stopped upon
closing Vim.

Default: `1`

```viml
let g:ycm_auto_stop_csharp_server = 1
```

### The `g:ycm_csharp_server_port` option

When g:ycm_auto_start_csharp_server is set to `1`, specifies the port for
the OmniSharp server to listen on. When set to `0` uses an unused port provided
by the OS.

Default: `0`

```viml
let g:ycm_csharp_server_port = 0
```

### The `g:ycm_csharp_insert_namespace_expr` option

By default, when YCM inserts a namespace, it will insert the `using` statement
under the nearest `using` statement. You may prefer that the `using` statement is
inserted somewhere, for example, to preserve sorting. If so, you can set this
option to override this behavior.

When this option is set, instead of inserting the `using` statement itself, YCM
will set the global variable `g:ycm_namespace_to_insert` to the namespace to
insert, and then evaluate this option's value as an expression. The option's
expression is responsible for inserting the namespace - the default insertion
will not occur.

Default: ''

```viml
let g:ycm_csharp_insert_namespace_expr = ''
```

### The `g:ycm_add_preview_to_completeopt` option

When this option is set to `1`, YCM will add the `preview` string to Vim's
`completeopt` option (see `:h completeopt`). If your `completeopt` option
already has `preview` set, there will be no effect. You can see the current
state of your `completeopt` setting with `:set completeopt?` (yes, the question
mark is important).

When `preview` is present in `completeopt`, YCM will use the `preview` window at
the top of the file to store detailed information about the current completion
candidate (but only if the candidate came from the semantic engine). For
instance, it would show the full function prototype and all the function
overloads in the window if the current completion is a function name.

Default: `0`

```viml
let g:ycm_add_preview_to_completeopt = 0
```

### The `g:ycm_autoclose_preview_window_after_completion` option

When this option is set to `1`, YCM will auto-close the `preview` window after
the user accepts the offered completion string. If there is no `preview` window
triggered because there is no `preview` string in `completeopt`, this option is
irrelevant. See the `g:ycm_add_preview_to_completeopt` option for more details.

Default: `0`

```viml
let g:ycm_autoclose_preview_window_after_completion = 0
```

### The `g:ycm_autoclose_preview_window_after_insertion` option

When this option is set to `1`, YCM will auto-close the `preview` window after
the user leaves insert mode. This option is irrelevant if
`g:ycm_autoclose_preview_window_after_completion` is set or if no `preview`
window is triggered. See the `g:ycm_add_preview_to_completeopt` option for more
details.

Default: `0`

```viml
let g:ycm_autoclose_preview_window_after_insertion = 0
```

### The `g:ycm_max_diagnostics_to_display` option

This option controls the maximum number of diagnostics shown to the user when
errors or warnings are detected in the file. This option is only relevant for
the C-family, C#, Java, JavaScript, and TypeScript languages.

A special value of `0` means there is no limit.

Default: `30`

```viml
let g:ycm_max_diagnostics_to_display = 30
```

### The `g:ycm_key_list_select_completion` option

This option controls the key mappings used to select the first completion
string.  Invoking any of them repeatedly cycles forward through the completion
list.

Some users like adding `<Enter>` to this list.

Default: `['<TAB>', '<Down>']`

```viml
let g:ycm_key_list_select_completion = ['<TAB>', '<Down>']
```

### The `g:ycm_key_list_previous_completion` option

This option controls the key mappings used to select the previous completion
string. Invoking any of them repeatedly cycles backwards through the completion
list.

Note that one of the defaults is `<S-TAB>` which means Shift-TAB. That mapping
will probably only work in GUI Vim (Gvim or MacVim) and not in plain console Vim
because the terminal usually does not forward modifier key combinations to Vim.

Default: `['<S-TAB>', '<Up>']`

```viml
let g:ycm_key_list_previous_completion = ['<S-TAB>', '<Up>']
```

### The `g:ycm_key_list_stop_completion` option

This option controls the key mappings used to close the completion menu. This is
useful when the menu is blocking the view, when you need to insert the `<TAB>`
character, or when you want to expand a snippet from [UltiSnips][] and navigate
through it.

Default: `['<C-y>']`

```viml
let g:ycm_key_list_stop_completion = ['<C-y>']
```

### The `g:ycm_key_invoke_completion` option

This option controls the key mapping used to invoke the completion menu for
semantic completion. By default, semantic completion is triggered automatically
after typing `.`, `->` and `::` in insert mode (if semantic completion support
has been compiled in). This key mapping can be used to trigger semantic
completion anywhere. Useful for searching for top-level functions and classes.

Console Vim (not Gvim or MacVim) passes `<Nul>` to Vim when the user types
`<C-Space>` so YCM will make sure that `<Nul>` is used in the map command when
you're editing in console Vim, and `<C-Space>` in GUI Vim. This means that you
can just press `<C-Space>` in both console and GUI Vim and YCM will do the right
thing.

Setting this option to an empty string will make sure no mapping is created.

Default: `<C-Space>`

```viml
let g:ycm_key_invoke_completion = '<C-Space>'
```

### The `g:ycm_key_detailed_diagnostics` option

This option controls the key mapping used to show the full diagnostic text when
the user's cursor is on the line with the diagnostic. It basically calls
`:YcmShowDetailedDiagnostic`.

Setting this option to an empty string will make sure no mapping is created.

Default: `<leader>d`

```viml
let g:ycm_key_detailed_diagnostics = '<leader>d'
```

### The `g:ycm_global_ycm_extra_conf` option

Normally, YCM searches for a `.ycm_extra_conf.py` file for compilation flags
(see the User Guide for more details on how this works). This option specifies
a fallback path to a config file which is used if no `.ycm_extra_conf.py` is
found.

You can place such a global file anywhere in your filesystem.

Default: `''`

```viml
let g:ycm_global_ycm_extra_conf = ''
```

### The `g:ycm_confirm_extra_conf` option

When this option is set to `1` YCM will ask once per `.ycm_extra_conf.py` file
if it is safe to be loaded. This is to prevent execution of malicious code
from a `.ycm_extra_conf.py` file you didn't write.

To selectively get YCM to ask/not ask about loading certain `.ycm_extra_conf.py`
files, see the `g:ycm_extra_conf_globlist` option.

Default: `1`

```viml
let g:ycm_confirm_extra_conf = 1
```

### The `g:ycm_extra_conf_globlist` option

This option is a list that may contain several globbing patterns. If a pattern
starts with a `!` all `.ycm_extra_conf.py` files matching that pattern will be
blacklisted, that is they won't be loaded and no confirmation dialog will be
shown. If a pattern does not start with a `!` all files matching that pattern
will be whitelisted. Note that this option is not used when confirmation is
disabled using `g:ycm_confirm_extra_conf` and that items earlier in the list
will take precedence over the later ones.

Rules:

* `*`       matches everything
* `?`       matches any single character
* `[seq]`   matches any character in seq
* `[!seq]`  matches any char not in seq

Example:

```viml
let g:ycm_extra_conf_globlist = ['~/dev/*','!~/*']
```

* The first rule will match everything contained in the `~/dev` directory so
  `.ycm_extra_conf.py` files from there will be loaded.
* The second rule will match everything in the home directory so a
  `.ycm_extra_conf.py` file from there won't be loaded.
* As the first rule takes precedence everything in the home directory excluding
  the `~/dev` directory will be blacklisted.

**NOTE:** The glob pattern is first expanded with Python's
`os.path.expanduser()` and then resolved with `os.path.abspath()` before being
matched against the filename.

Default: `[]`

```viml
let g:ycm_extra_conf_globlist = []
```

### The `g:ycm_filepath_completion_use_working_dir` option

By default, YCM's filepath completion will interpret relative paths like `../`
as being relative to the folder of the file of the currently active buffer.
Setting this option will force YCM to always interpret relative paths as being
relative to Vim's current working directory.

Default: `0`

```viml
let g:ycm_filepath_completion_use_working_dir = 0
```

### The `g:ycm_semantic_triggers` option

This option controls the character-based triggers for the various semantic
completion engines. The option holds a dictionary of key-values, where the keys
are Vim's filetype strings delimited by commas and values are lists of strings,
where the strings are the triggers.

Setting key-value pairs on the dictionary _adds_ semantic triggers to the
internal default set (listed below). You cannot remove the default triggers,
only add new ones.

A "trigger" is a sequence of one or more characters that trigger semantic
completion when typed. For instance, C++ (`cpp` filetype) has `.` listed as a
trigger. So when the user types `foo.`, the semantic engine will trigger and
serve `foo`'s list of member functions and variables. Since C++ also has `->`
listed as a trigger, the same thing would happen when the user typed `foo->`.

It's also possible to use a regular expression as a trigger. You have to prefix
your trigger with `re!` to signify it's a regex trigger. For instance,
`re!\w+\.` would only trigger after the `\w+\.` regex matches.

**NOTE:** The regex syntax is **NOT** Vim's, it's [Python's][python-re].

Default: `[see next line]`

```viml
let g:ycm_semantic_triggers =  {
  \   'c': ['->', '.'],
  \   'objc': ['->', '.', 're!\[[_a-zA-Z]+\w*\s', 're!^\s*[^\W\d]\w*\s',
  \            're!\[.*\]\s'],
  \   'ocaml': ['.', '#'],
  \   'cpp,cuda,objcpp': ['->', '.', '::'],
  \   'perl': ['->'],
  \   'php': ['->', '::'],
  \   'cs,d,elixir,go,groovy,java,javascript,julia,perl6,python,scala,typescript,vb': ['.'],
  \   'ruby,rust': ['.', '::'],
  \   'lua': ['.', ':'],
  \   'erlang': [':'],
  \ }
```

### The `g:ycm_cache_omnifunc` option

Some omnicompletion engines do not work well with the YCM cache—in particular,
they might not produce all possible results for a given prefix. By unsetting
this option you can ensure that the omnicompletion engine is re-queried on every
keypress. That will ensure all completions will be presented, but might cause
stuttering and lagginess if the omnifunc is slow.

Default: `1`

```viml
let g:ycm_cache_omnifunc = 1
```

### The `g:ycm_use_ultisnips_completer` option

By default, YCM will query the UltiSnips plugin for possible completions of
snippet triggers. This option can turn that behavior off.

Default: `1`

```viml
let g:ycm_use_ultisnips_completer = 1
```

### The `g:ycm_goto_buffer_command` option

Defines where `GoTo*` commands result should be opened. Can take one of the
following values: `'same-buffer'`, `'split'`, or `'split-or-existing-window'`.
If this option is set to the `'same-buffer'` but current buffer can not be
switched (when buffer is modified and `nohidden` option is set), then result
will be opened in a split. When the option is set to
`'split-or-existing-window'`, if the result is already open in a window of the
current tab page (or any tab pages with the `:tab` modifier; see below), it will
jump to that window. Otherwise, the result will be opened in a split as if the
option was set to `'split'`.

To customize the way a new window is split, prefix the `GoTo*` command with one
of the following modifiers: `:aboveleft`, `:belowright`, `:botright`,
`:leftabove`, `:rightbelow`, `:topleft`, and `:vertical`. For instance, to
split vertically to the right of the current window, run the command:
```viml
:rightbelow vertical YcmCompleter GoTo
```

To open in a new tab page, use the `:tab` modifier with the `'split'` or
`'split-or-existing-window'` options e.g.:
```viml
:tab YcmCompleter GoTo
```

**NOTE:** command modifiers were added in Vim 7.4.1898. If you are using an
older version, you can still configure this by setting the option to one of the
deprecated values: `'vertical-split'`, `'new-tab'`, or `'new-or-existing-tab'`.

Default: `'same-buffer'`

```viml
let g:ycm_goto_buffer_command = 'same-buffer'
```

### The `g:ycm_disable_for_files_larger_than_kb` option

Defines the max size (in Kb) for a file to be considered for completion. If this
option is set to 0 then no check is made on the size of the file you're opening.

Default: 1000

```viml
let g:ycm_disable_for_files_larger_than_kb = 1000
```

### The `g:ycm_use_clangd` option

This option controls whether **clangd** should be used as completion engine for
C-family languages. Can take one of the following values: `1`, `0`, with
meanings:

- `1`: YCM will use clangd if clangd binary exists in third party or it was
provided with `ycm_clangd_binary_path` option.
- `0`: YCM will never use clangd completer.

Default: `1`

```viml
let g:ycm_use_clangd = 1
```

### The `g:ycm_clangd_binary_path` option

When `ycm_use_clangd` option is set to `1`, this option sets the path to
**clangd** binary.

Default: `''`

```viml
let g:ycm_clangd_binary_path = ''
```

### The `g:ycm_clangd_args` option

This option controls the command line arguments passed to the clangd binary. It
appends new options and overrides the existing ones.

Default: `[]`

```viml
let g:ycm_clangd_args = []
```

### The `g:ycm_clangd_uses_ycmd_caching` option

This option controls which ranking and filtering algorithm to use for completion
items. It can take values:

- `1`: Uses ycmd's caching and filtering logic.
- `0`: Uses clangd's caching and filtering logic.

Default: `1`

```viml
let g:ycm_clangd_uses_ycmd_caching = 1
```

FAQ
---

### I used to be able to `import vim` in `.ycm_extra_conf.py`, but now can't

YCM was rewritten to use a client-server architecture where most of the logic is
in the [ycmd server][ycmd]. So the magic `vim` module you could have previously
imported in your `.ycm_extra_conf.py` files doesn't exist anymore.

To be fair, importing the magic `vim` module in extra conf files was never
supported in the first place; it only ever worked by accident and was never a
part of the extra conf API.

But fear not, you should be able to tweak your extra conf files to continue
working by using the `g:ycm_extra_conf_vim_data` option. See the docs on that
option for details.

### I get `ImportError` exceptions that mention `PyInit_ycm_core` or `initycm_core`

These errors are caused by building the YCM native libraries for Python 2 and
trying to load them into a Python 3 process (or the other way around).

For instance, if building for Python 2 but loading in Python 3:

```
ImportError: dynamic module does not define init function (PyInit_ycm_core)
```

If building for Python 3 but loading in Python 2:

```
ImportError: dynamic module does not define init function (initycm_core)
```

Setting the `g:ycm_server_python_interpreter` option to force the use of a
specific Python interpreter for `ycmd` is usually the easiest way to solve the
problem. Common values for that option are `/usr/bin/python` and
`/usr/bin/python3`.

### I get a linker warning regarding `libpython` on Mac when compiling YCM

If the warning is `ld: warning: path '/usr/lib/libpython2.7.dylib' following -L
not a directory`, then feel free to ignore it; it's caused by a limitation of
CMake and is not an issue. Everything should still work fine.

### I get a weird window at the top of my file when I use the semantic engine

This is Vim's `preview` window. Vim uses it to show you extra information about
something if such information is available. YCM provides Vim with such extra
information. For instance, when you select a function in the completion list,
the `preview` window will hold that function's prototype and the prototypes of
any overloads of the function. It will stay there after you select the
completion so that you can use the information about the parameters and their
types to write the function call.

If you would like this window to auto-close after you select a completion
string, set the `g:ycm_autoclose_preview_window_after_completion` option to `1`
in your `vimrc` file. Similarly, the `g:ycm_autoclose_preview_window_after_insertion`
option can be set to close the `preview` window after leaving insert mode.

If you don't want this window to ever show up, add `set completeopt-=preview` to
your `vimrc`. Also make sure that the `g:ycm_add_preview_to_completeopt` option
is set to `0`.

### It appears that YCM is not working

In Vim, run `:messages` and carefully read the output. YCM will echo messages to
the message log if it encounters problems. It's likely you misconfigured
something and YCM is complaining about it.

Also, you may want to run the `:YcmDebugInfo` command; it will make YCM spew out
various debugging information, including the YCM and [ycmd][] logfile paths and
the compile flags for the current file if the file is a C-family language file
and you have compiled in Clang support. Logfiles can be opened in the editor
using [the `:YcmToggleLogs` command](#the-ycmtogglelogs-command).

### Sometimes it takes much longer to get semantic completions than normal

This means that libclang (which YCM uses for C-family semantic completion)
failed to pre-compile your file's preamble. In other words, there was an error
compiling some of the source code you pulled in through your header files. I
suggest calling the `:YcmDiags` command to see what they were.

Bottom line, if libclang can't pre-compile your file's preamble because there
were errors in it, you're going to get slow completions because there's no AST
cache.

### YCM auto-inserts completion strings I don't want!

If this happens when Vim automatically wraps text then it's a Vim bug that has
been fixed in version 8.0.0127. Update your Vim to this version or later.

This could also be some mappings that interfere with YCM's internal ones. Make
sure you don't have something mapped to `<C-p>`, `<C-x>` or `<C-u>` (in insert
mode).

YCM _never_ selects something for you; it just shows you a menu and the user has
to explicitly select something. If something is being selected automatically,
this means there's a bug or a misconfiguration somewhere.

### I get a `E227: mapping already exists for <blah>` error when I start Vim

This means that YCM tried to set up a key mapping but failed because you already
had something mapped to that key combination. The `<blah>` part of the message
will tell you what was the key combination that failed.

Look in the _Options_ section and see if any of the default mappings conflict
with your own. Then change that option value to something else so that the
conflict goes away.

### I get `'GLIBC_2.XX' not found (required by libclang.so)` when starting Vim

Your system is too old for the precompiled binaries from llvm.org. Compile
Clang on your machine and then link against the `libclang.so` you just produced.
See the full installation guide for help.

### I'm trying to use a Homebrew Vim with YCM and I'm getting segfaults

Something (I don't know what) is wrong with the way that Homebrew configures and
builds Vim. I recommend using [MacVim][]. Even if you don't like the MacVim GUI,
you can use the Vim binary that is inside the MacVim.app package (it's
`MacVim.app/Contents/MacOS/Vim`) and get the Vim console experience.

### I have a Homebrew Python and/or MacVim; can't compile/SIGABRT when starting

You should probably run `brew rm python; brew install python` to get the latest
fixes that should make YCM work with such a configuration. Also rebuild Macvim
then. If you still get problems with this, see [issue #18][issue18] for
suggestions.

### I get `LONG_BIT definition appears wrong for platform` when compiling

Look at the output of your CMake call. There should be a line in it like the
following (with `.dylib` in place of `.so` on a Mac):

```
-- Found PythonLibs: /usr/lib/libpython2.7.so (Required is at least version "2.5")
```

That would be the **correct** output. An example of **incorrect** output would
be the following:

```
-- Found PythonLibs: /usr/lib/libpython2.7.so (found suitable version "2.5.1", minimum required is "2.5")
```

Notice how there's an extra bit of output there, the `found suitable version
"<version>"` part, where `<version>` is not the same as the version of the
dynamic library. In the example shown, the library is version 2.7 but the second
string is version `2.5.1`.

This means that CMake found one version of Python headers and a different
version for the library. This is wrong. It can happen when you have multiple
versions of Python installed on your machine.

You should probably add the following flags to your cmake call (again, `dylib`
instead of `so` on a Mac):

```
-DPYTHON_INCLUDE_DIR=/usr/include/python2.7 -DPYTHON_LIBRARY=/usr/lib/libpython2.7.so
```

This will force the paths to the Python include directory and the Python library
to use. You may need to set these flags to something else, but you need to make
sure you use the same version of Python that your Vim binary is built against,
which is highly likely to be the system's default Python.

### I get `libpython2.7.a [...] relocation R_X86_64_32` when compiling

The error is usually encountered when compiling YCM on Centos or RHEL. The full
error looks something like the following:

```
/usr/bin/ld: /usr/local/lib/libpython2.7.a(abstract.o): relocation R_X86_64_32 against `a local symbol' can not be used when making a shared object; recompile with -fPIC
```

It's possible to get a slightly different error that's similar to the one above.
Here's the problem and how you solve it:

Your `libpython2.7.a` was not compiled with `-fPIC` so it can't be linked into
`ycm_core.so`.  Use the `-DPYTHON_LIBRARY=` CMake flag to point it to a `.so`
version of libpython on your machine (for instance,
`-DPYTHON_LIBRARY=/usr/lib/libpython2.7.so`). Naturally, this means you'll have
to go through the full installation guide by hand.

### I see `undefined symbol: clang_getCompletionFixIt` in the server logs.

This means that the server is trying to load a version of libclang that is too
old. You need at least libclang 7.0.0. We recommend running the `install.py`
script without `--system-libclang` or downloading the [latest prebuilt binaries
from llvm.org][clang-download] when going through the [full installation
guide](#full-installation-guide).

### I get `Fatal Python error: PyThreadState_Get: no current thread` on startup

This is caused by linking a static version of `libpython` into ycmd's
`ycm_core.so`.  This leads to multiple copies of the python interpreter loaded
when `python` loads `ycmd_core.so` and this messes up python's global state.
The details aren't important.

The solution is that the version of Python linked and run against must be built
with either `--enable-shared` or `--enable-framework` (on OS X).
This is achieved as follows (**NOTE:** for Mac, replace `--enable-shared`
with `--enable-framework`):

- When building python from source: `./configure --enable-shared {options}`
- When building python from pyenv:
  `PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install {version}`


### `install.py` says python must be compiled with `--enable-framework`. Wat?

See the previous answer for how to ensure your python is built to support
dynamic modules.

### YCM does not read identifiers from my tags files

First, put `let g:ycm_collect_identifiers_from_tags_files = 1` in your vimrc.

Make sure you are using [Exuberant Ctags][exuberant-ctags] to produce your tags
files since the only supported tag format is the [Exuberant Ctags
format][ctags-format]. The format from "plain" ctags is NOT supported. The
output of `ctags --version` should list "Exuberant Ctags". See [Universal
Ctags][universal-ctags] for a maintained version.

Ctags needs to be called with the `--fields=+l` (that's a lowercase `L`, not a
one) option because YCM needs the `language:<lang>` field in the tags output.

**NOTE:** [Exuberant Ctags][exuberant-ctags] by default sets language tag for
`*.h` files as `C++`. If you have C (not C++) project, consider giving parameter
`--langmap=c:.c.h` to ctags to see tags from `*.h` files.

**NOTE:** Mac OS X comes with "plain" ctags installed by default. `brew install
ctags` will get you the Exuberant Ctags version.

Also make sure that your Vim `tags` option is set correctly. See `:h 'tags'` for
details. If you want to see which tag files YCM will read for a given buffer,
run `:echo tagfiles()` with the relevant buffer active. Note that that function
will only list tag files that already exist.

### `CTRL-U` in insert mode does not work while the completion menu is visible

YCM uses `completefunc` completion mode to show suggestions and Vim disables
`<C-U>` in that mode as a "feature." Sadly there's nothing I can do about this.

### My `CTRL-R` mapping does not work while the completion menu is visible

Vim prevents remapping of the `<C-R>` key in all `<C-X>` completion modes
(except the `<C-X><C-N>`/`<C-X><C-P>` mode which operates in the same mode as
`<C-N>`/`<C-P>`) and YCM uses the `<C-X><C-U>` (`completefunc`) mode for
completions. This means that adding `<C-R>` to any of the `g:ycm_key_list_*`
options has no effect. You need to use another key.

### YCM conflicts with UltiSnips TAB key usage

YCM comes with support for UltiSnips (snippet suggestions in the popup menu),
but you'll have to change the UltiSnips mappings. See `:h UltiSnips-triggers` in
Vim for details. You'll probably want to change some/all of the following
options:

```viml
g:UltiSnipsExpandTrigger
g:UltiSnipsJumpForwardTrigger
g:UltiSnipsJumpBackwardTrigger
```

### Snippets added with `:UltiSnipsAddFiletypes` do not appear in the popup menu

For efficiency, YCM only fetches UltiSnips snippets in specific scenarios like
visiting a buffer or setting its filetype. You can force YCM to retrieve them by
manually triggering the `FileType` autocommand:

```viml
:doautocmd FileType
```

### Why isn't YCM just written in plain VimScript, FFS?

Because of the identifier completion engine and subsequence-based filtering.
Let's say you have _many_ dozens of files open in a single Vim instance (I often
do); the identifier-based engine then needs to store thousands (if not tens of
thousands) of identifiers in its internal data-structures. When the user types,
YCM needs to perform subsequence-based filtering on _all_ of those identifiers
(every single one!) in less than 10 milliseconds.

I'm sorry, but that level of performance is just plain impossible to achieve
with VimScript. I've tried, and the language is just too slow. No, you can't get
acceptable performance even if you limit yourself to just the identifiers in the
current file and simple prefix-based filtering.

### Why does YCM demand such a recent version of Vim?

YCM needs a version of Vim with the timers feature to achieve full
asynchronicity. This feature is available since Vim 7.4.1578.

### Nasty bugs happen if I have the `vim-autoclose` plugin installed

Use the [delimitMate][] plugin instead. It does the same thing without
conflicting with YCM.

### Is there some sort of YCM mailing list? I have questions

If you have questions about the plugin or need help, please use the
[ycm-users][] mailing list, _don't_ create issues on the tracker. The tracker is
for bug reports and feature requests.

### I get an internal compiler error when installing

This can be a problem on virtual servers with limited memory. A possible
solution is to add more swap memory. A more practical solution would be to force
the build script to run only one compile job at a time. You can do this by
setting the `YCM_CORES` environment variable to `1`. Example:

```
YCM_CORES=1 ./install.py --clang-completer
```

### I get weird errors when I press `Ctrl-C` in Vim

_Never_ use `Ctrl-C` in Vim.

Using `Ctrl-C` to exit insert mode in Vim is a bad idea. The main issue here is
that `Ctrl-C` in Vim doesn't just leave insert mode, it leaves it without
triggering `InsertLeave` autocommands (as per Vim docs). This is a bad idea and
is likely to break many other things and not just YCM.

Bottom line, if you use `Ctrl-C` to exit insert mode in Vim, you're gonna have a
bad time.

If pressing `<esc>` is too annoying (agreed, it is), we suggest mapping it to
something more convenient. On a QWERTY keyboard, a good pick for the `<esc>` map
is `inoremap jk <Esc>`. This is right on the home row, it's an incredibly rare
digraph in English and if you ever need to type those two chars in sequence in
insert mode, you just type `j`, then wait 500ms, then type `k`.

### Why did YCM stop using Syntastic for diagnostics display?

Previously, YCM would send any diagnostics it would receive from the libclang
semantic engine to Syntastic for display as signs in the gutter, red squiggles
etc. Today, YCM uses its own code to do that.

Using Syntastic for this was always a kludge. Syntastic assumes its "checker"
plugins behave in a certain way; those assumptions have never fit YCM. For
instance, YCM continuously recompiles your code in the background for C-family
languages and tries to push new diagnostics to the user as fast as possible,
even while the user types.

Syntastic assumes that a checker only runs on file save ("active" mode) or even
less frequently, when the user explicitly invokes it ("passive" mode). This
mismatch in assumptions causes performance problems since Syntastic code isn't
optimized for this use case of constant diagnostic refreshing.

Poor support for this use case also led to crash bugs in Vim caused by
Syntastic-Vim interactions ([issue #593][issue-593]) and other problems, like
random Vim flickering. Attempts were made to resolve these issues in
Syntastic, but ultimately some of them failed (for various reasons).

Implementing diagnostic display code directly in YCM resolves all of these
problems. Performance also improved substantially since the relevant code is now
written in Python instead of VimScript (which is very slow) and is tailored only
for YCM's use-cases. We were also able to introduce new features in this area
since we're now not limited to the Syntastic checker API.

We've tried to implement this in the most backwards-compatible way possible; YCM
options that control diagnostic display fall back to Syntastic options that
control the same concepts if the user has those set.

Still, some Syntastic-specific configuration you might have had might not
be supported by the new code. Please file issues on the tracker in such
cases; if we find the request to be reasonable, we'll find a way to address it.

### Completion doesn't work with the C++ standard library headers

This is caused by an issue with libclang that only affects some operating
systems. Compiling with `clang` the binary will use the correct default header
search paths but compiling with `libclang.so` (which YCM uses) does not.

Mac OS X is normally affected, but there's a workaround in YCM for that specific
OS. If you're not running that OS but still have the same problem, continue
reading.

The workaround is to call `echo | clang -v -E -x c++ -` and look at the
paths under the `#include <...> search starts here:` heading. You should take
those paths, prepend `-isystem` to each individual path and append them all to
the list of flags you return from your `Settings` function in your
`.ycm_extra_conf.py` file.

See [issue #303][issue-303] for details.

### When I start vim I get a runtime error saying `R6034 An application has made an attempt to load the C runtime library incorrectly.`

[CMake and other things seem to screw up the PATH with their own msvcrXX.dll
versions.][identify-R6034-cause] Add the following to the very top of your vimrc
to remove these entries from the path.

```python
python << EOF
import os
import re
path = os.environ['PATH'].split(';')

def contains_msvcr_lib(folder):
    try:
        for item in os.listdir(folder):
            if re.match(r'msvcr\d+\.dll', item):
                return True
    except:
        pass
    return False

path = [folder for folder in path if not contains_msvcr_lib(folder)]
os.environ['PATH'] = ';'.join(path)
EOF
```

### I hear that YCM only supports Python 2, is that true?

**No.** Both the Vim client and the [ycmd server][ycmd] run on Python 2 or 3. If
you are talking about code completion in a project, you can configure the Python
used for your project through a `.ycm_extra_conf.py` file. See [the Python
Semantic Completion section](#python-semantic-completion) for more details.

### On Windows I get `E887: Sorry, this command is disabled, the Python's site module could not be loaded`

If you are running vim on Windows with Python 2.7.11, this is likely caused by a
[bug][vim_win-python2.7.11-bug]. Follow this
[workaround][vim_win-python2.7.11-bug_workaround] or use a different version
(Python 2.7.12 does not suffer from the bug).

### I can't complete Python packages in a virtual environment.

This means that the Python used to run [Jedi][] is not the Python of the virtual
environment you're in. To resolve this you should create a `.ycm_extra_conf.py`
file at the root of your project that sets the `interpreter_path` option to the
Python of your virtual environment, e.g.

```python
def Settings(**kwargs):
  return {
    'interpreter_path': '/path/to/virtual/env/bin/python'
  }
```

See [the Python Semantic Completion section](#python-semantic-completion) for
more details.

### I want to defer loading of YouCompleteMe until after Vim finishes booting

In recent versions of Vim, you can install YCM in a folder under
`~/.vim/pack/*/opt` and then load it once the user is idle via an autocommand:

```viml
augroup load_ycm
  autocmd!
  autocmd CursorHold, CursorHoldI * :packadd YouCompleteMe
                                \ | autocmd! load_ycm
augroup END
```

### YCM does not shut down when I quit Vim

YCM relies on the `VimLeave` event to shut down the [ycmd server][ycmd]. Some
plugins prevent this event from triggering by exiting Vim through an autocommand
without using the `nested` keyword (see `:h autocmd-nested`). You should
identify which plugin is responsible for the issue and report it to the plugin
author. Note that when this happens, [ycmd][] will automatically shut itself
down after 30 minutes.

### YCM does not work with my Anaconda Python setup

Anaconda is often incompatible with the pre-built libclang used by YCM
and therefore is not supported. The recommended way to solve this is to run
`/path/to/real/python install.py` (for example `/usr/bin/python install.py`).

If you want completion in Anaconda projects, point the `interpreter_path` option
in your `.ycm_extra_conf.py` file to the path of your Anaconda Python e.g.

```python
def Settings(**kwargs):
  return {
    'interpreter_path': '/path/to/anaconda/python'
  }
```

See [the Python Semantic Completion section](#python-semantic-completion) for
more details.

### Automatic import insertion after selecting a completion breaks undo

This is a Vim bug fixed in version 8.1.0256. Update your Vim to this version or
later.

### `TAB` is already mapped to trigger completion in the command-line window

Vim automatically maps the key set by the `wildchar` option, which is `TAB` by
default, to complete commands in the command-line window. If you would prefer
using this key to cycle through YCM's suggestions without changing the value of
`wildchar`, add the following to your vimrc:

```viml
autocmd CmdwinEnter * inoremap <expr><buffer> <TAB>
      \ pumvisible() ? "\<C-n>" : "\<TAB>"
```

Contributor Code of Conduct
---------------------------

Please note that this project is released with a [Contributor Code of
Conduct][ccoc]. By participating in this project you agree to abide by its
terms.


Contact
-------

If you have questions about the plugin or need help, please join the [Gitter
room][gitter] or use the [ycm-users][] mailing list.

If you have bug reports or feature suggestions, please use the [issue
tracker][tracker]. Before you do, please carefully read
[CONTRIBUTING.md][contributing-md] as this asks for important diagnostics which
the team will use to help get you going.

The latest version of the plugin is available at
<http://valloric.github.io/YouCompleteMe/>.

The author's homepage is <http://val.markovic.io>.

Please do **NOT** go to #vim on freenode for support. Please contact the
YouCompleteMe maintainers directly using the [contact details](#contact).

License
-------

This software is licensed under the [GPL v3 license][gpl].
© 2015-2018 YouCompleteMe contributors

[ycmd]: https://github.com/Valloric/ycmd
[Clang]: http://clang.llvm.org/
[vundle]: https://github.com/VundleVim/Vundle.vim#about
[pathogen]: https://github.com/tpope/vim-pathogen#pathogenvim
[clang-download]: http://llvm.org/releases/download.html
[brew]: http://brew.sh
[cmake-download]: https://cmake.org/download/
[macvim]: https://github.com/macvim-dev/macvim/releases
[vimrc]: http://vimhelp.appspot.com/starting.txt.html#vimrc
[gpl]: http://www.gnu.org/copyleft/gpl.html
[vim]: http://www.vim.org/
[syntastic]: https://github.com/scrooloose/syntastic
[lightline]: https://github.com/itchyny/lightline.vim
[ycm_flags_example]: https://github.com/Valloric/YouCompleteMe/blob/master/.ycm_extra_conf.py
[ycmd_flags_example]: https://raw.githubusercontent.com/Valloric/ycmd/66030cd94299114ae316796f3cad181cac8a007c/.ycm_extra_conf.py
[compdb]: http://clang.llvm.org/docs/JSONCompilationDatabase.html
[subsequence]: https://en.wikipedia.org/wiki/Subsequence
[listtoggle]: https://github.com/Valloric/ListToggle
[vim-build]: https://github.com/Valloric/YouCompleteMe/wiki/Building-Vim-from-source
[tracker]: https://github.com/Valloric/YouCompleteMe/issues?state=open
[issue18]: https://github.com/Valloric/YouCompleteMe/issues/18
[delimitMate]: https://github.com/Raimondi/delimitMate
[completer-api]: https://github.com/Valloric/ycmd/blob/master/ycmd/completers/completer.py
[eclim]: http://eclim.org/
[jedi]: https://github.com/davidhalter/jedi
[ultisnips]: https://github.com/SirVer/ultisnips/blob/master/doc/UltiSnips.txt
[exuberant-ctags]: http://ctags.sourceforge.net/
[universal-ctags]: https://github.com/universal-ctags/ctags
[ctags-format]: http://ctags.sourceforge.net/FORMAT
[vundle-bug]: https://github.com/VundleVim/Vundle.vim/issues/48
[ycm-users]: https://groups.google.com/forum/?hl=en#!forum/ycm-users
[omnisharp]: https://github.com/OmniSharp/omnisharp-server
[issue-303]: https://github.com/Valloric/YouCompleteMe/issues/303
[issue-593]: https://github.com/Valloric/YouCompleteMe/issues/593
[issue-669]: https://github.com/Valloric/YouCompleteMe/issues/669
[status-mes]: https://groups.google.com/forum/#!topic/vim_dev/WeBBjkXE8H8
[python-re]: https://docs.python.org/2/library/re.html#regular-expression-syntax
[Bear]: https://github.com/rizsotto/Bear
[ygen]: https://github.com/rdnetto/YCM-Generator
[Gocode]: https://github.com/nsf/gocode
[Godef]: https://github.com/Manishearth/godef
[TSServer]: https://github.com/Microsoft/TypeScript/tree/master/src/server
[jsconfig.json]: https://code.visualstudio.com/docs/languages/jsconfig
[tsconfig.json]: https://www.typescriptlang.org/docs/handbook/tsconfig-json.html
[vim-win-download]: https://github.com/vim/vim-win32-installer/releases
[python-win-download]: https://www.python.org/downloads/windows/
[visual-studio-download]: https://www.visualstudio.com/downloads/
[7z-download]: http://www.7-zip.org/download.html
[mono-install-osx]: http://www.mono-project.com/docs/getting-started/install/mac/
[mono-install-linux]: https://www.mono-project.com/download/stable/#download-lin
[mono-install]: http://www.mono-project.com/docs/getting-started/install/
[go-install]: https://golang.org/doc/install
[npm-install]: https://docs.npmjs.com/getting-started/installing-node#1-install-nodejs--npm
[tern-instructions]: https://github.com/Valloric/YouCompleteMe/wiki/JavaScript-Semantic-Completion-through-Tern
[Tern]: http://ternjs.net
[racer]: https://github.com/phildawes/racer
[rust-install]: https://www.rust-lang.org/
[rust-src]: https://www.rust-lang.org/downloads.html
[add-msbuild-to-path]: http://stackoverflow.com/questions/6319274/how-do-i-run-msbuild-from-the-command-line-using-windows-sdk-7-1
[identify-R6034-cause]: http://stackoverflow.com/questions/14552348/runtime-error-r6034-in-embedded-python-application/34696022
[ccoc]: https://github.com/Valloric/YouCompleteMe/blob/master/CODE_OF_CONDUCT.md
[vim_win-python2.7.11-bug]: https://github.com/vim/vim/issues/717
[vim_win-python2.7.11-bug_workaround]: https://github.com/vim/vim-win32-installer/blob/a27bbdba9bb87fa0e44c8a00d33d46be936822dd/appveyor.bat#L86-L88
[gitter]: https://gitter.im/Valloric/YouCompleteMe
[ninja-compdb]: https://ninja-build.org/manual.html
[++enc]: http://vimdoc.sourceforge.net/htmldoc/editing.html#++enc
[rustup]: https://www.rustup.rs/
[contributing-md]: https://github.com/Valloric/YouCompleteMe/blob/master/CONTRIBUTING.md
[jdt.ls]: https://github.com/eclipse/eclipse.jdt.ls
[jdk-install]: http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html
[mvn-project]: https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html
[eclipse-project]: https://help.eclipse.org/oxygen/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Freference%2Fmisc%2Fproject_description_file.html
[gradle-project]: https://docs.gradle.org/current/userguide/tutorial_java_projects.html
[eclipse-dot-project]: https://help.eclipse.org/oxygen/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Freference%2Fmisc%2Fproject_description_file.html
[eclipse-dot-classpath]: https://help.eclipse.org/mars/index.jsp?topic=%2Forg.eclipse.jdt.doc.isv%2Freference%2Fapi%2Forg%2Feclipse%2Fjdt%2Fcore%2FIClasspathEntry.html
[ycmd-eclipse-project]: https://github.com/Valloric/ycmd/tree/3602f38ef7a762fc765afd75e562aec9a134711e/ycmd/tests/java/testdata/simple_eclipse_project
[ycmd-mvn-pom-xml]: https://github.com/Valloric/ycmd/blob/3602f38ef7a762fc765afd75e562aec9a134711e/ycmd/tests/java/testdata/simple_maven_project/pom.xml
[ycmd-gradle-project]: https://github.com/Valloric/ycmd/tree/3602f38ef7a762fc765afd75e562aec9a134711e/ycmd/tests/java/testdata/simple_gradle_project
[jdtls-release]: http://download.eclipse.org/jdtls/milestones
[diacritic]: https://www.unicode.org/glossary/#diacritic
[regex]: https://pypi.org/project/regex/
[clangd]: https://clang.llvm.org/extra/clangd.html
[fixedcdb]: https://clang.llvm.org/docs/JSONCompilationDatabase.html#alternatives
[clangd-indexing]: https://clang.llvm.org/extra/clangd.html#project-wide-indexing
