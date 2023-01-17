YouCompleteMe: a code-completion engine for Vim
===============================================

[![Gitter room](https://img.shields.io/gitter/room/Valloric/YouCompleteMe.svg)](https://gitter.im/Valloric/YouCompleteMe)
[![Build status](https://dev.azure.com/YouCompleteMe/YCM/_apis/build/status/ycm-core.YouCompleteMe?branchName=master)](https://dev.azure.com/YouCompleteMe/YCM/_build?definitionId=3&branchName=master)
[![Coverage status](https://img.shields.io/codecov/c/github/ycm-core/YouCompleteMe/master.svg)](https://codecov.io/gh/ycm-core/YouCompleteMe)

Help, Advice, Support
---------------------

Looking for help, advice or support? Having problems getting YCM to work?

First carefully read the [installation instructions](#installation) for your OS.
We recommend you use the supplied `install.py` - the "full" installation guide
is for rare, advanced use cases and most users should use `install.py`.

If the server isn't starting and you're getting a "YouCompleteMe unavailable"
error, check the [Troubleshooting][wiki-troubleshooting] guide.

Next check the [User Guide](#user-guide) section on the semantic completer that
you are using. For C/C++/Objective-C/Objective-C++/CUDA, you  _must_ read [this
section](#c-family-semantic-completion).

Finally, check the [FAQ][wiki-faq].

If, after reading the installation and user guides, and checking the FAQ, you're
still having trouble, check the [contacts](#contact) section below for how to
get in touch.

Please do **NOT** go to #vim on Freenode for support. Please contact the
YouCompleteMe maintainers directly using the [contact details](#contact) below.

Contents
--------

- [Intro](#intro)
- [Installation](#installation)
    - [Requirements](#requirements)
    - [macOS](#macos)
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
    - [Signature Help](#signature-help)
    - [Semantic Highlighting](#semantic-highlighting)
    - [Inlay Hints](#inlay-hints)
    - [C-family Semantic Completion](#c-family-semantic-completion)
    - [Java Semantic Completion](#java-semantic-completion)
    - [C# Semantic Completion](#c-semantic-completion)
    - [Python Semantic Completion](#python-semantic-completion)
    - [Rust Semantic Completion](#rust-semantic-completion)
    - [Go Semantic Completion](#go-semantic-completion)
    - [JavaScript and TypeScript Semantic Completion](#javascript-and-typescript-semantic-completion)
    - [Semantic Completion for Other Languages](#semantic-completion-for-other-languages)
    - [LSP Configuration](#lsp-configuration)
    - [Writing New Semantic Completers](#writing-new-semantic-completers)
    - [Diagnostic Display](#diagnostic-display)
        - [Diagnostic Highlighting Groups](#diagnostic-highlighting-groups)
    - [Symbol Search](#symbol-search)
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
- [Sponsorship](#sponsorship)


Intro
-----

YouCompleteMe is a fast, as-you-type, fuzzy-search code completion,
comprehension and refactoring engine for [Vim][].

It has several completion engines built in and supports any protocol-compliant
Language Server, so can work with practically any language. YouCompleteMe
contains:

- an identifier-based engine that works with every programming language,
- a powerful [clangd][]-based engine that provides native semantic code
  completion for C/C++/Objective-C/Objective-C++/CUDA (from now on referred to
  as "the C-family languages"),
- a [Jedi][]-based completion engine for Python 2 and 3,
- an [OmniSharp-Roslyn][]-based completion engine for C#,
- a [Gopls][]-based completion engine for Go,
- a [TSServer][]-based completion engine for JavaScript and TypeScript,
- a [rust-analyzer][]-based completion engine for Rust,
- a [jdt.ls][]-based completion engine for Java.
- a [generic Language Server Protocol implementation for any language](#plugging-an-arbitrary-lsp-server)
- and an omnifunc-based completer that uses data from Vim's omnicomplete system
  to provide semantic completions for many other languages (Ruby, PHP etc.).

![YouCompleteMe GIF completion demo](https://i.imgur.com/0OP4ood.gif)

Here's an explanation of what happens in the last GIF demo above.

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

**And that's not all...**

YCM might be the only Vim completion engine with the correct Unicode support.
Though we do assume UTF-8 everywhere.

![YouCompleteMe GIF unicode demo](https://user-images.githubusercontent.com/10026824/34471853-af9cf32a-ef53-11e7-8229-de534058ddc4.gif)

YCM also provides [semantic IDE-like features](#quick-feature-summary) in a
number of languages, including:

- displaying signature help (argument hints) when entering the arguments to a
  function call (Vim only)
- [finding declarations, definitions, usages](#goto-commands), etc.
  of identifiers, and an [interactive symbol finder](#symbol-search)
- [displaying type information](#the-gettype-subcommand) for classes,
  variables, functions etc.,
- displaying documentation for methods, members, etc. in the [preview
  window](#the-getdoc-subcommand), or in a
  [popup next to the cursor](#the-gycm_auto_hover-option) (Vim only)
- [fixing common coding errors](#the-fixit-subcommand), like missing
  semi-colons, typos, etc.,
- [semantic renaming](#the-refactorrename-subcommand) of variables across files,
- formatting code,
- removing unused imports, sorting imports, etc.

For example, here's a demo of signature help:

![Signature Help Early Demo](https://user-images.githubusercontent.com/10584846/58738348-5060da80-83fd-11e9-9537-d07fdbf4554c.gif)

Below we can see YCM being able to do a few things:

- Retrieve references across files
- Go to declaration/definition
- Expand `auto` in C++
- Fix some common errors, and provide refactorings, with `FixIt`
- Not shown in the GIF is `GoToImplementation` and `GoToType`
  for servers that support it.

![YouCompleteMe GIF subcommands demo](https://i.imgur.com/nmUUbdl.gif)

And here's some documentation being shown in a hover popup, automatically and
manually:

![hover demo](https://user-images.githubusercontent.com/10584846/80312146-91af6500-87db-11ea-996b-7396f3134d1f.gif)

Features vary by file type, so make sure to check out the [file type feature
summary](#quick-feature-summary) and the
[full list of completer subcommands](#ycmcompleter-subcommands) to
find out what's available for your favourite languages.

You'll also find that YCM has filepath completers (try typing `./` in a file)
and a completer that integrates with [UltiSnips][].

Installation
------------

### Requirements

| Runtime | Min Version | Recommended Version (full support) | Python |
|---------|-------------|------------------------------------|--------|
| Vim     | 8.1.2269    | 9.0.214                            | 3.8    |
| Neovim  | 0.5         | Vim 9.0.214                        | 3.8    |

#### Supported Vim Versions

Our policy is to support the Vim version that's in the latest LTS of Ubuntu.
That's currently Ubuntu 20.04 which contains `vim-nox` at `v8.1.2269`.

Vim must have a [working Python 3 runtime](#supported-python-runtime).

For Neovim users, our policy is to require the latest released version.
Currently, Neovim 0.5.0 is required.  Please note that some features are not
available in Neovim, and Neovim is not officially supported.

#### Supported Python runtime

YCM has two components: A server and a client. Both the server and client
require Python 3.8 or later 3.x release. 

For the Vim client, Vim must be, compiled with `--enable-shared` (or
`--enable-framework` on macOS). You can check if this is working with `:py3
import sys; print( sys.version)`. It should say something like `3.8.2 (...)`.

For Neovim, you must have a python 3.8 runtime and the Neovim python
extensions. See Neovim's `:help provider-python` for how to set that up.

For the server, you must run the `install.py` script with a python 3.8 (or
later) runtime. Anaconda etc. are not supported. YCM will remember the runtime
you used to run `install.py` and will use that when launching the server, so if
you usually use anaconda, then make sure to use the full path to a real cpython3,
e.g. `/usr/bin/python3 install.py --all` etc.

Our policy is to support the python3 version that's availble in the latest
Ubuntu LTS (similar to our Vim version policy). We don't increase the python
runtime version without a reason, though. Typically, we do this when the current
python version wer're using goes out of support. At that time we will typically
pick a version that will be supported for a number of years.

#### Supported Compilers

In order to provide the best possible performance and stability, ycmd has
updated its code to C++17. This requires a version bump of the minimum
supported compilers. The new requirements are:

| Compiler | Current Min    |
|----------|----------------|
| GCC      | 8              |
| Clang    | 7              |
| MSVC     | 15.7 (VS 2017) |

YCM requires CMake 3.13 or greater. If your CMake is too old, you may be able to
simply `pip install --user cmake` to get a really new version.

#### Individual completer requirements

When enabling language support for a particular language, there may be runtime
requirements, such as needing a very recent Java Development Kit for Java
support. In general, YCM is not in control of the required versions for the
downstream compilers, though we do our best to signal where we know them.

### macOS

#### Quick start, installing all completers

- Install YCM plugin via [Vundle][]
- Install CMake, MacVim and Python 3; Note that the pre-installed *macOS system*
  Vim is not supported (due to it having broken Python integration).

```
$ brew install cmake python go nodejs
```

- Install mono from [Mono Project](mono-install-macos) (NOTE: on Intel Macs you
  can also `brew install mono`. On arm Macs, you may require Rosetta)

- For java support you must install a JDK, one way to do this is with Homebrew:

```
$ brew install java
$ sudo ln -sfn $(brew --prefix java)/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
```

- Pre-installed macOS *system* Vim does not support Python 3. So you need to
  install either a Vim that supports Python 3 OR [MacVim][] with
  [Homebrew][brew]:

  - Option 1: Installing a Vim that supports Python 3
  
  ```
  brew install vim
  ```

  - Option 2: Installing [MacVim][]
  
  ```
  brew install macvim
  ```

- Compile YCM.

  - For Intel and arm64 Macs, the bundled libclang/clangd work:

    ```
    cd ~/.vim/bundle/YouCompleteMe
    python3 install.py --all
    ```

  - If you have troubles with finding system frameworks or C++ standard library,
    try using the homebrew llvm:

    ```
    brew install llvm
    cd ~/.vim/bundle/YouCompleteMe
    python3 install.py --system-libclang --all
    ```

    And edit your vimrc to add the following line to use the Homebrew llvm's
    clangd:

    ```viml
    " Use homebrew's clangd
    let g:ycm_clangd_binary_path = trim(system('brew --prefix llvm')).'/bin/clangd'
    ```


- For using an arbitrary LSP server, check [the relevant
  section](#plugging-an-arbitrary-lsp-server)

#### Explanation for the quick start

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

A supported Vim version with Python 3 is required. [MacVim][] is a good option,
even if you only use the terminal. YCM won't work with the pre-installed Vim
from Apple as its Python support is broken. If you don't already use a Vim
that supports Python 3 or [MacVim][], install it with [Homebrew][brew]. Install
CMake as well:

    brew install vim cmake     
    
   OR

    brew install macvim cmake

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the `ycm_core` library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

**NOTE:** If you want C-family completion, you MUST have the latest Xcode
installed along with the latest Command Line Tools (they are installed
automatically when you run `clang` for the first time, or manually by running
`xcode-select --install`)

Compiling YCM **with** semantic support for C-family languages through
**clangd**:

```
cd ~/.vim/bundle/YouCompleteMe
./install.py --clangd-completer
```

Compiling YCM **without** semantic support for C-family languages:

```
cd ~/.vim/bundle/YouCompleteMe
./install.py
```


The following additional language support options are available:

- C# support: install by downloading the [Mono macOS package][mono-install-macos]
  and add `--cs-completer` when calling `install.py`.
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: add `--rust-completer` when calling `install.py`.
- Java support: install [JDK 17][jdk-install] and add
  `--java-completer` when calling `install.py`.

To simply compile with everything enabled, there's a `--all` flag. So, to
install with all language features, ensure `xbuild`, `go`, `node` and `npm`
tools are installed and in your `PATH`, then simply run:

```
cd ~/.vim/bundle/YouCompleteMe
./install.py --all
```

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### Linux 64-bit

The following assume you're using Ubuntu 20.04.

#### Quick start, installing all completers

- Install YCM plugin via [Vundle][]
- Install CMake, Vim and Python

```
apt install build-essential cmake vim-nox python3-dev
```

- Install mono-complete, go, node, java and npm

```
apt install mono-complete golang nodejs openjdk-17-jdk openjdk-17-jre npm
```

- Compile YCM

```
cd ~/.vim/bundle/YouCompleteMe
python3 install.py --all
```

- For plugging an arbitrary LSP server, check [the relevant section](#plugging-an-arbitrary-lsp-server)

#### Explanation for the quick start

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

Make sure you have a supported version of Vim with Python 3 support, and a
supported compiler. The latest LTS of Ubuntu is the minimum platform for simple
installation. For earlier releases or other distributions, you may have to do
some work to acquire the dependencies.

If your Vim version is too old, you may need to [compile Vim from
source][vim-build] (don't worry, it's easy).

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the `ycm_core` library APIs have changed (happens rarely), YCM
will notify you to recompile it. You should then rerun the install process.

Install development tools, CMake, and Python headers:

- Fedora-like distributions:

```
sudo dnf install cmake gcc-c++ make python3-devel
```

- Ubuntu LTS:

```
sudo apt install build-essential cmake3 python3-dev
```

Compiling YCM **with** semantic support for C-family languages through
**clangd**:

```
cd ~/.vim/bundle/YouCompleteMe
python3 install.py --clangd-completer
```

Compiling YCM **without** semantic support for C-family languages:

```
cd ~/.vim/bundle/YouCompleteMe
python3 install.py
```

The following additional language support options are available:

- C# support: install [Mono][mono-install-linux] and add `--cs-completer`
  when calling `install.py`.
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: add `--rust-completer` when calling `install.py`.
- Java support: install [JDK 17][jdk-install] and add
  `--java-completer` when calling `install.py`.

To simply compile with everything enabled, there's a `--all` flag. So, to
install with all language features, ensure `xbuild`, `go`, `node` and `npm`
tools are installed and in your `PATH`, then simply run:

```
cd ~/.vim/bundle/YouCompleteMe
python3 install.py --all
```

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### Windows

#### Quick start, installing all completers

- Install YCM plugin via [Vundle][]
- Install [Visual Studio Build Tools 2019][visual-studio-download]
- Install CMake, Vim and Python
- Install go, node and npm
- Compile YCM

```
cd YouCompleteMe
python3 install.py --all
```

- Add `set encoding=utf-8` to your [vimrc][]
- For plugging an arbitrary LSP server, check [the relevant section](#plugging-an-arbitrary-lsp-server)

#### Explanation for the quick start

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

**Important:** we assume that you are using the `cmd.exe` command prompt and
that you know how to add an executable to the PATH environment variable.

Make sure you have a supported Vim version with Python 3 support. You
can check the version and which Python is supported by typing `:version` inside
Vim. Look at the features included: `+python3/dyn` for Python 3.
Take note of the Vim architecture, i.e. 32 or
64-bit. It will be important when choosing the Python installer. We recommend
using a 64-bit client. [Daily updated installers of 32-bit and 64-bit Vim with
Python 3 support][vim-win-download] are available.

Add the following line to your [vimrc][] if not already present.:

```viml
set encoding=utf-8
```

This option is required by YCM. Note that it does not prevent you from editing a
file in another encoding than UTF-8.  You can do that by specifying [the `++enc`
argument][++enc] to the `:e` command.

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the `ycm_core` library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

Download and install the following software:

- [Python 3][python-win-download]. Be sure to pick the version
  corresponding to your Vim architecture. It is _Windows x86_ for a 32-bit Vim
  and _Windows x86-64_ for a 64-bit Vim. We recommend installing Python 3.
  Additionally, the version of Python you install must match up exactly with
  the version of Python that Vim is looking for. Type `:version` and look at the
  bottom of the page at the list of compiler flags. Look for flags that look
  similar to `-DDYNAMIC_PYTHON3_DLL=\"python36.dll\"`. This indicates
  that Vim is looking for Python 3.6. You'll need one or the other installed,
  matching the version number exactly.
- [CMake][cmake-download]. Add CMake executable to the PATH environment
  variable.
- [Build Tools for Visual Studio 2019][visual-studio-download]. During setup,
  select _C++ build tools_ in _Workloads_.

Compiling YCM **with** semantic support for C-family languages through
**clangd**:

```
cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
python install.py --clangd-completer
```

Compiling YCM **without** semantic support for C-family languages:

```
cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
python install.py
```

The following additional language support options are available:

- C# support: add `--cs-completer` when calling `install.py`.
  Be sure that [the build utility `msbuild` is in your PATH][add-msbuild-to-path].
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: add `--rust-completer` when calling `install.py`.
- Java support: install [JDK 17][jdk-install] and add
  `--java-completer` when calling `install.py`.

To simply compile with everything enabled, there's a `--all` flag. So, to
install with all language features, ensure `msbuild`, `go`, `node` and `npm`
tools are installed and in your `PATH`, then simply run:

```
cd %USERPROFILE%/vimfiles/bundle/YouCompleteMe
python install.py --all
```

You can specify the Microsoft Visual C++ (MSVC) version using the `--msvc`
option. YCM officially supports MSVC 15 (2017), MSVC 16 (Visual Studio 2019) 
and MSVC 17 (Visual Studio 17 2022).

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### FreeBSD/OpenBSD

#### Quick start, installing all completers

- Install YCM plugin via [Vundle][]
- Install CMake

```
pkg install cmake
```

- Install xbuild, go, node and npm
- Compile YCM

```
cd ~/.vim/bundle/YouCompleteMe
python3 install.py --all
```

- For plugging an arbitrary LSP server, check [the relevant section](#plugging-an-arbitrary-lsp-server)

#### Explanation for the quick start

These instructions (using `install.py`) are the quickest way to install
YouCompleteMe, however they may not work for everyone. If the following
instructions don't work for you, check out the [full installation
guide](#full-installation-guide).

**NOTE:** OpenBSD / FreeBSD are not officially supported platforms by YCM.

Make sure you have a supported Vim version with Python 3 support, and a supported
compiler and CMake, perhaps:

```
pkg install cmake
```

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the `ycm_core` library APIs have changed (happens
rarely), YCM will notify you to recompile it. You should then rerun the install
process.

Compiling YCM **with** semantic support for C-family languages through
**clangd**:

```
cd ~/.vim/bundle/YouCompleteMe
./install.py --clangd-completer
```

Compiling YCM **without** semantic support for C-family languages:

```
cd ~/.vim/bundle/YouCompleteMe
./install.py
```

If the `python` executable is not present, or the default `python` is not the
one that should be compiled against, specify the python interpreter explicitly:

```
python3 install.py --clangd-completer
```

The following additional language support options are available:

- C# support: install Mono and add `--cs-completer` when calling
  `./install.py`.
- Go support: install [Go][go-install] and add `--go-completer` when calling
  `./install.py`.
- JavaScript and TypeScript support: install [Node.js and npm][npm-install] and
  add `--ts-completer` when calling `install.py`.
- Rust support: add `--rust-completer` when calling `./install.py`.
- Java support: install [JDK 17][jdk-install] and add
  `--java-completer` when calling `./install.py`.

To simply compile with everything enabled, there's a `--all` flag. So, to
install with all language features, ensure `xbuild`, `go`, `node` and `npm`
tools are installed and in your `PATH`, then simply run:

```
cd ~/.vim/bundle/YouCompleteMe
./install.py --all
```

That's it. You're done. Refer to the _User Guide_ section on how to use YCM.
Don't forget that if you want the C-family semantic completion engine to work,
you will need to provide the compilation flags for your project to YCM. It's all
in the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

### Full Installation Guide

The [full installation guide][wiki-full-install] has been moved to the wiki.

Quick Feature Summary
-----

### General (all languages)

* Super-fast identifier completer including tags files and syntax elements
* Intelligent suggestion ranking and filtering
* File and path suggestions
* Suggestions from Vim's omnifunc
* UltiSnips snippet suggestions

### C-family languages (C, C++, Objective C, Objective C++, CUDA)

* Semantic auto-completion with automatic fixes
* Signature help
* Real-time diagnostic display
* Go to include/declaration/definition (`GoTo`, etc.)
* Go to alternate file (e.g. associated header `GoToAlternateFile`)
* Find Symbol (`GoToSymbol`), with interactive search
* Document outline (`GoToDocumentOutline`), with interactive search
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors (`FixIt`)
* Perform refactoring (`FixIt`)
* Reference finding (`GoToReferences`)
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)
* Semantic highlighting
* Inlay hints

### C♯

* Semantic auto-completion
* Signature help
* Real-time diagnostic display
* Go to declaration/definition (`GoTo`, etc.)
* Go to implementation (`GoToImplementation`)
* Find Symbol (`GoToSymbol`), with interactive search
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors (`FixIt`)
* Perform refactoring (`FixIt`)
* Management of OmniSharp-Roslyn server instance
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)

### Python

* Semantic auto-completion
* Signature help
* Go to definition (`GoTo`)
* Find Symbol (`GoToSymbol`), with interactive search
* Reference finding (`GoToReferences`)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Renaming symbols (`RefactorRename <new name>`)

### Go

* Semantic auto-completion
* Signature help
* Real-time diagnostic display
* Go to declaration/definition (`GoTo`, etc.)
* Go to type definition (`GoToType`)
* Go to implementation (`GoToImplementation`)
* Document outline (`GoToDocumentOutline`), with interactive search
* Automatically fix certain errors (`FixIt`)
* Perform refactoring (`FixIt`)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Code formatting (`Format`)
* Management of `gopls` server instance

### JavaScript and TypeScript

* Semantic auto-completion with automatic import insertion
* Signature help
* Real-time diagnostic display
* Go to definition (`GoTo`, `GoToDefinition`, and `GoToDeclaration` are
  identical)
* Go to type definition (`GoToType`)
* Go to implementation (`GoToImplementation`)
* Find Symbol (`GoToSymbol`), with interactive search
* Reference finding (`GoToReferences`)
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors and perform refactoring (`FixIt`)
* Perform refactoring (`FixIt`)
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)
* Organize imports (`OrganizeImports`)
* Management of `TSServer` server instance
* Inlay hints

### Rust

* Semantic auto-completion
* Real-time diagnostic display
* Go to declaration/definition (`GoTo`, etc.)
* Go to implementation (`GoToImplementation`)
* Reference finding (`GoToReferences`)
* Document outline (`GoToDocumentOutline`), with interactive search
* View documentation comments for identifiers (`GetDoc`)
* Automatically fix certain errors (`FixIt`)
* Perform refactoring (`FixIt`)
* Type information for identifiers (`GetType`)
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)
* Management of `rust-analyzer` server instance
* Semantic highlighting
* Inlay hints

### Java

* Semantic auto-completion with automatic import insertion
* Signature help
* Real-time diagnostic display
* Go to definition (`GoTo`, `GoToDefinition`, and `GoToDeclaration` are
  identical)
* Go to type definition (`GoToType`)
* Go to implementation (`GoToImplementation`)
* Find Symbol (`GoToSymbol`), with interactive search
* Reference finding (`GoToReferences`)
* Document outline (`GoToDocumentOutline`), with interactive search
* View documentation comments for identifiers (`GetDoc`)
* Type information for identifiers (`GetType`)
* Automatically fix certain errors including code generation (`FixIt`)
* Renaming symbols (`RefactorRename <new name>`)
* Code formatting (`Format`)
* Organize imports (`OrganizeImports`)
* Detection of java projects
* Execute custom server command (`ExecuteCommand <args>`)
* Management of `jdt.ls` server instance
* Semantic highlighting

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
using console Vim (that is, not gvim or MacVim) then it's likely that the
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

### Signature Help

Valid signatures are displayed in a second popup menu and the current signature
is highlighted along with the current argument.

Signature help is triggered in insert mode automatically when
`g:ycm_auto_trigger` is enabled and is not supported when it is not enabled.

The signatures popup is hidden when there are no matching signatures or when you
leave insert mode. There is no key binding to clear the popup.

For more details on this feature and a few demos, check out the
[PR that proposed it][signature-help-pr].

#### Dismiss signature help

The signature help popup sometimes gets in the way. You can toggle its
visibility with a mapping. YCM provides the "Plug" mapping
`<Plug>(YCMToggleSignatureHelp)` for this.

For example, to hide/show the signature help popup by pressing Ctrl+l in insert
mode: `imap <silent> <C-l> <Plug>(YCMToggleSignatureHelp)`.

_NOTE_: No default mapping is provided because insert mappings are very
difficult to create without breaking or overriding some existing functionality.
Ctrl-l is not a suggestion, just an example.

### Semantic highlighting

**NOTE**: This feature is highly experimental and offered in the hope that it is
useful. It shall not be considered stable; if you find issues with it, feel free
to report them however.

Semantic highlighting is the process where the buffer text is coloured according
to the underlying semantic type of the word, rather than classic syntax
highlighting based on regular expressions. This can be powerful additional data
that we can process very quickly.

This feature is only supported in Vim.

For example, here is a function with classic highlighting:

![highliting-classic](https://user-images.githubusercontent.com/10584846/173137003-a265e8b0-84db-4993-98f0-03ee81b9de94.png)

And here is the same function with semantic highlighting:

![highliting-semantic](https://user-images.githubusercontent.com/10584846/173137012-7547de0b-145f-45fa-ace3-18943acd2141.png)

As you can see, the function calls, macros, etc. are correctly identified. 

This can be enabled globally with `let g:ycm_enable_semantic_highlighting=1` or
per buffer, by setting `b:ycm_enable_semantic_highlighting`.

#### Customising the highlight groups

YCM uses text properties (see `:help text-prop-intro`) for semantic
highlighting. In order to customise the coloring, you can define the text
properties that are used.

If you define a text property named `YCM_HL_<token type>`, then it will be used
in place of the defaults. The `<token type>` is defined as the Language Server
Protocol semantic token type, defined in the [LSP Spec](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_semanticTokens).

Some servers also use custom values. In this case, YCM prints a warning
including the token type name that you can customise.

For example, to render `parameter` tokens using the `Normal` highlight group,
you can do this:

```viml
call prop_type_add( 'YCM_HL_parameter', { 'highlight': 'Normal' } )
```

More generally, this pattern can be useful for customising the groups:

```viml
let MY_YCM_HIGHLIGHT_GROUP = {
      \   'typeParameter': 'PreProc',
      \   'parameter': 'Normal',
      \   'variable': 'Normal',
      \   'property': 'Normal',
      \   'enumMember': 'Normal',
      \   'event': 'Special',
      \   'member': 'Normal',
      \   'method': 'Normal',
      \   'class': 'Special',
      \   'namespace': 'Special',
      \ }

for tokenType in keys( MY_YCM_HIGHLIGHT_GROUP )
  call prop_type_add( 'YCM_HL_' . tokenType,
                    \ { 'highlight': MY_YCM_HIGHLIGHT_GROUP[ tokenType ] } )
endfor
```

## Inlay hints

**NOTE**: Highly experimental feature, requiring Vim 9.0.214 or later (not
supported in NeoVim).

When `g:ycm_enable_inlay_hints` (globally) or `b:ycm_enable_inlay_hints` (for a
specific buffer) is set to `1`, then YCM will insert inlay hints as supported by
the language semantic engine.

An inlay hint is text rendered on the screen which is not part of the buffer and
is often used to mark up the type or name of arguments, parameters, etc. which
help the developer understand the semantics of the code.

Here are some examples:

* C

![c-inlay](https://user-images.githubusercontent.com/10584846/185708054-68074fc0-e50c-4a65-887c-da6f372b8982.png)

* TypeScript

![ts-inlay](https://user-images.githubusercontent.com/10584846/185708156-b52970ce-005f-4f0b-97e7-bdf8feeefedc.png)

* Go

![go-inlay](https://user-images.githubusercontent.com/10584846/185708242-e42dab6f-1847-46f1-8585-2d9f2c8a76dc.png)

### Highlight groups

By default, YCM renders the inlay hints with the `NonText` highlight group. To
override this, define the `YcmInlayHint` highlight yourself, e.g. in your
`.vimrc`:

```viml
hi link YcmInlayHint Comment
```

Similar to semantic highlighting above, you can override specific highlighting
for different inlay hint types by defining text properties named after the kind
of inlay hint, for example:

```viml
call prop_type_add( 'YCM_INLAY_Type', #{ highlight: 'Comment' } )
```

The list of inlay hint kinds can be found in `python/ycm/inlay_hints.py`

### Options

* `g:ycm_enable_inlay_hints` or `b:ycm_enable_inlay_hints` - enable/disable
  globally or for local buffer
* `g:ycm_clear_inlay_hints_in_insert_mode` - set to `1` to remove all inlay
  hints when entering insert mode and reinstate them when leaving insert mode

### Toggling

Inlay hints can add a lot of text to the screen and may be distracting. You can
toggle them on/off instantly, by mapping something to
`<Plug>(YCMToggleInlayHints)`, for example:

```viml
nnoremap <silent> <localleader>h <Plug>(YCMToggleInlayHints)
```

No default mapping is provided for this due to the personal nature of mappings.

### General Semantic Completion

You can use Ctrl+Space to trigger the completion suggestions anywhere, even
without a string prefix. This is useful to see which top-level functions are
available for use.

### C-family Semantic Completion

**NOTE:** YCM originally used the `libclang` based engine for C-family, but
users should migrate to clangd, as it provides more features and better
performance. Users who rely on `override_filename` in their `.ycm_extra_conf.py`
will need to stay on the old `libclang` engine. Instructions on how to stay on
the old engine are available on [the wiki][libclang-instructions].

Some of the features of clangd:

- **Project wide indexing**: Clangd has both dynamic and static index support.
  The dynamic index stores up-to-date symbols coming from any files you are
  currently editing, whereas static index contains project-wide symbol
  information. This symbol information is used for code completion and code
  navigation. Whereas libclang is limited to the current translation unit(TU).
- **Code navigation**: Clangd provides all the GoTo requests libclang provides and it
  improves those using the above mentioned index information to contain
  project-wide information rather than just the current TU.
- **Rename**: Clangd can perform semantic rename operations on the current
  file, whereas libclang doesn't support such functionality.
- **Code Completion**: Clangd can perform code completions at a lower latency
  than libclang; also, it has information about all the symbols in your
  project so it can suggest items outside your current TU and also provides
  proper `#include` insertions for those items.
- **Signature help**: Clangd provides signature help so that you can see the
  names and types of arguments when calling functions.
- **Format Code**: Clangd provides code formatting either for the selected
  lines or the whole file, whereas libclang doesn't have such functionality.
- **Performance**: Clangd has faster re-parse and code completion times
  compared to libclang.

#### Installation

On supported architectures, the `install.py` script will download a suitable
clangd (`--clangd-completer`) or libclang (`--clang-completer`) for you.
Supported architectures are:

* Linux glibc >= 2.27 (Intel, armv7-a, aarch64) - built on ubuntu 18.04
* MacOS >=10.15 (Intel, arm64)
  - For Intel, compatibility per clang.llvm.org downloads
  - For arm64, macOS 10.15+
* Windows (Intel) - compatibility per clang.llvm.org downloads

***clangd***:

Typically, clangd is installed by the YCM installer (either with `--all` or with
`--clangd-completer`). This downloads a pre-built `clangd` binary for your
architecture. If your OS or architecture is not supported or too old, you can
install a compatible `clangd` and use [`g:ycm_clangd_binary_path`]() to point to
it.

***libclang***:

`libclang` can be enabled also with `--all` or `--clang-completer`. As with
`clangd`, YCM will try and download a version of `libclang` that is suitable for
your environment, but again if your environment can't be supported, you can
build or acquire `libclang` for yourself and specify it when building, as:

```
$ EXTRA_CMAKE_ARGS='-DPATH_TO_LLVM_ROOT=/path/to/your/llvm' ./install.py --clang-completer --system-libclang
```

Please note that if using custom `clangd` or `libclang` it _must_ match the
version that YCM requires. Currently YCM requires ***clang 15.0.1***.

#### Compile flags

In order to perform semantic analysis such as code completion, `GoTo` and
diagnostics, YouCompleteMe uses `clangd`, which makes use of
clang compiler, sometimes also referred to as LLVM. Like any compiler,
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
- If using GNU make, check out [compiledb][] or [Bear][].
- For other build systems, check out
  [`.ycm_extra_conf.py`](#option-2-provide-the-flags-manually) below.

If no [`.ycm_extra_conf.py`](#option-2-provide-the-flags-manually) is found,
YouCompleteMe automatically tries to load a compilation database if there is
one.

YCM looks for a file named `compile_commands.json` in the directory of the
opened file or in any directory above it in the hierarchy (recursively); when
the file is found before a local `.ycm_extra_conf.py`, YouCompleteMe stops
searching the directories and lets clangd take over and handle the flags.

#### Option 2: Provide the flags manually

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

### Java Semantic Completion

#### Java quick Start

1. Ensure that you have enabled the Java completer. See the
   [installation guide](#installation) for details.

2. Create a project file (gradle or maven) file in the root directory of your
   Java project, by following the instructions below.

3. (Optional) [Configure the LSP server](#lsp-configuration). The [jdt.ls
   configuration options][jdtls-preferences] can be found in their codebase.

4. If you previously used Eclim or Syntastic for Java, disable them for Java.

5. Edit a Java file from your project.

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

Some users have experienced issues with their jdt.ls  when using the Groovy
language for their build.gradle. As such, try using
[Kotlin](https://github.com/ycm-core/lsp-examples#kotlin) instead.

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

### C# Semantic Completion

YCM relies on [OmniSharp-Roslyn][] to provide completion and code navigation.
OmniSharp-Roslyn needs a solution file for a C# project and there are two ways
of letting YCM know about your solution files.

#### Automatically discovered solution files

YCM will scan all parent directories of the file currently being edited and look
for file with `.sln` extension.

#### Manually specified solution files

If YCM loads `.ycm_extra_conf.py` which contains `CSharpSolutionFile` function,
YCM will try to use that to determine the solution file. This is useful when one
wants to override the default behaviour and specify a solution file that is not
in any of the parent directories of the currently edited file. Example:

```python
def CSharpSolutionFile( filepath ):
  # `filepath` is the path of the file user is editing
  return '/path/to/solution/file' # Can be relative to the `.ycm_extra_conf.py`
```

If the path returned by `CSharpSolutionFile` is not an actual file, YCM will
fall back to the other way of finding the file.

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

Here, `/path/to/virtual/environment/python` is the path to the Python used
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
instance, the following `.ycm_extra_conf.py` adds the paths
`/path/to/some/third_party/package` and `/path/to/another/third_party/package`
at the start of `sys.path`:

```python
def Settings( **kwargs ):
  return {
    'sys_path': [
      '/path/to/some/third_party/package',
      '/path/to/another/third_party/package'
    ]
  }
```

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

Then, create the `~/global_extra_conf.py` file with the following contents:

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

YCM uses [rust-analyzer][] for Rust semantic completion.

NOTE: Previously, YCM used [rls][] for rust completion. This is no longer
supported, as the Rust community has decided on [rust-analyzer][] as the future
of Rust tooling.

Completions and GoTo commands within the current crate and its dependencies
should work out of the box with no additional configuration (provided that you
built YCM with the `--rust-completer` flag; see the [*Installation*
section](#installation) for details). The install script takes care of
installing [the Rust source code][rust-src], so no configuration is necessary.

`rust-analyzer` supports a myriad of options. These are configured using [LSP
configuration](#lsp-configuration), and are [documented here](https://rust-analyzer.github.io/manual.html#configuration]).

### Go Semantic Completion

Completions and GoTo commands should work out of the box (provided that you
built YCM with the `--go-completer` flag; see the [*Installation*
section](#installation) for details). The server only works for projects with
the "canonical" layout.

`gopls` also has a handful of undocumented options for which the
[source code][gopls-preferences] is the only reference.

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
supported natively by YouCompleteMe using the [Clang][], [OmniSharp-Roslyn][],
[Gopls][], [jdt.ls][], [Jedi][], [rust-analyzer][], and [TSServer][] engines,
respectively. Check the [installation](#installation) section for instructions
to enable these features if desired.

#### Plugging an arbitrary LSP server

Similar to other LSP clients, YCM can use an arbitrary LSP server with the help
of [`g:ycm_language_server`](#the-gycm_language_server-option) option. An
example of a value of this option would be:

```viml
let g:ycm_language_server = 
  \ [ 
  \   {
  \     'name': 'yaml',
  \     'cmdline': [ '/path/to/yaml/server/yaml-language-server', '--stdio' ],
  \     'filetypes': [ 'yaml' ]
  \   },
  \   {
  \     'name': 'rust',
  \     'cmdline': [ 'ra_lsp_server' ],
  \     'filetypes': [ 'rust' ],
  \     'project_root_files': [ 'Cargo.toml' ]
  \   },
  \   {
  \     'name': 'godot',
  \     'filetypes': [ 'gdscript' ],
  \     'port': 6008,
  \     'project_root_files': [ 'project.godot' ]
  \    }
  \ ]
```

Each dictionary contains the following keys:

* `name` (string, mandatory): When [configuring a LSP
  server](#lsp-configuration) the value of the `name` key will be used as the
  `kwargs[ 'language' ]`. Can be anything you like.
* `filetypes` (list of string, mandatory): List of Vim filetypes this server
  should be used for.
* `project_root_files` (list of string, optional): List of filenames to search
  for when trying to determine the project root.
* `cmdline` (list of string, optional): If supplied, the server is started with
  this command line (each list element is a command line word). Typically, the
  server should be started with STDIO communication. If not supplied, `port`
  must be supplied.
* `port` (number, optional): If supplied, ycmd will connect to the server at
  `localhost:<port>` using TCP (remote servers are not supported).
* `capabilities` (dict, optional): If supplied, this is a dictionary that is
  merged with the LSP client capabilities reported to the language server. This
  can be used to enable or disable certain features, such as the support for
  configuration sections (`workspace/configuration`).

See [the LSP Examples](https://github.com/ycm-core/lsp-examples) project for more
examples of configuring the likes of PHP, Ruby, Kotlin, and D.

#### LSP Configuration

Many LSP servers allow some level of user configuration. YCM enables this with
the help of `.ycm_extra_conf.py` files. Here's an example of jdt.ls user
examples of configuring the likes of PHP, Ruby, Kotlin, D, and many, many more.

```python
def Settings( **kwargs ):
  if kwargs[ 'language' ] == 'java':
    return {
      'ls': {
        'java.format.onType.enabled': True
      }
    }
```

The `ls` key tells YCM that the dictionary should be passed to the LSP server.
For each of the LSP server's configuration you should look up the respective
server's documentation.

Some servers request settings from arbitrary 'sections' of configuration. There
is no concept of configuration sections in Vim, so you can specify an additional
`config_sections` dictionary which maps section to a dictionary of config
required by the server. For example:

```python
def Settings( **kwargs ):
  if kwargs[ 'language' ] == 'java':
    return {
      'ls': {
        'java.format.onType.enabled': True
      },
      'config_sections': {
        'some section': {
          'some option': 'some value'
        }
    }
```

The sections and options/values are complete server-specific and rarely well
documented.

#### Using `omnifunc` for semantic completion

YCM will use your `omnifunc` (see `:h omnifunc` in Vim) as a source for semantic
completions if it does not have a native semantic completion engine for your
file's filetype. Vim comes with rudimentary omnifuncs for various languages like
Ruby, PHP, etc. It depends on the language.

You can get a stellar omnifunc for Ruby with [Eclim][]. Just make sure you have
the _latest_ Eclim installed and configured (this means Eclim `>= 2.2.*` and
Eclipse `>= 4.2.*`).

After installing Eclim remember to create a new Eclipse project within your
application by typing `:ProjectCreate <path-to-your-project> -n ruby` inside Vim
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

YCM will display diagnostic notifications for the C-family, C#, Go, Java,
JavaScript, Rust and TypeScript languages. Since YCM continuously recompiles
your file as you type, you'll get notified of errors and warnings in your file
as fast as possible.

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
set the `signcolumn` option to `no` in your vimrc:

```viml
set signcolumn=no
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

### Symbol Search

***This feature requires Vim and is not supported in Neovim***

YCM provides a way to search for and jump to a symbol in the current project or
document when using supported languages.

You can search for symbols in the current workspace when the `GoToSymbol`
request is supported and the current document when `GoToDocumentOutline` is
supported.

Here's a quick demo: 

[![asciicast](https://asciinema.org/a/4JmYLAaz5hOHbZDD0hbsQpY8C.svg)](https://asciinema.org/a/4JmYLAaz5hOHbZDD0hbsQpY8C)

As you can see, you can type and YCM filters down the list as you type. The
current set of matches are displayed in a popup window in the centre of the
screen and you can select an entry with the keyboard, to jump to that position.
Any matches are then added to the quickfix list.

To enable:

* `nmap <something> <Plug>(YCMFindSymbolInWorkspace)`
* `nmap <something> <Plug>(YCMFindSymbolInDocument)`

e.g.

* `nmap <leader>yfw <Plug>(YCMFindSymbolInWorkspace)`
* `nmap <leader>yfd <Plug>(YCMFindSymbolInDocument)`

When searching, YCM opens a prompt buffer at the top of the screen for the
input, and puts you in insert mode. This means that you can hit `<Esc>` to go
into normal mode and use any other input commands that are supported in prompt
buffers. As you type characters, the search is updated.

Intially, results are queried from all open filetypes. You can hit `<C-f>` to
switch to just the current filetype while the popup is open.

While the popup is open, the following keys are intercepted:

* `<C-j>`, `<Down>`, `<C-n>`, `<Tab>` - select the next item
* `<C-k>`, `<Up>`, `<C-p>`, `<S-Tab>` - select the previous item
* `<PageUp>`, `<kPageUp>` - jump up one screenful of items 
* `<PageDown>`, `<kPageDown>` - jump down one screenful of items
* `<Home>`, `<kHome>` - jump to first item
* `<End>`, `<kEnd>` - jump to last item
* `<CR>` - jump to the selected item
* `<C-c>` cancel/dismiss the popup
* `<C-f>` - toggle results from all file types or just the current filetype

The search is also cancelled if you leave the prompt buffer window at any time,
so you can use window commands `<C-w>...` for example.

#### Closing the popup

***NOTE***: Pressing `<Esc>` does not close the popup - you must use `Ctrl-c`
for that, or use a window command (e.g. `<Ctrl-w>j`) or the mouse to leave the
prompt buffer window.

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

An options argument can be passed. If the argument is `popup` the diagnostic
text will be displayed in a popup at cursor position.

If you prefer the detailed diagnostic to always be shown in a popup, then
`let g:ycm_show_detailed_diag_in_popup=1`.

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

#### The `GoToAlternateFile` subcommand

Jump to the associated file, as defined by the language server. Typically this
will jump you to the associated header file for a c or c++ translation unit.

Supported in filetypes: `c, cpp, objc, objcpp, cuda` (clangd only)

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

#### The `GoToSymbol <symbol query>` subcommand

Finds the definition of all symbols matching a specified string. Note that this
does not use any sort of smart/fuzzy matching. However, an [interactive symbol
search](#symbol-search) is also available.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, java, javascript, python, typescript`

#### The `GoToReferences` subcommand

This command attempts to find all of the references within the project to the
identifier under the cursor and populates the quickfix list with those
locations.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, java, javascript, python, typescript, rust`

#### The `GoToImplementation` subcommand

Looks up the symbol under the cursor and jumps to its implementation (i.e.
non-interface). If there are multiple implementations, instead provides a list
of implementations to choose from.

Supported in filetypes: `cs, go, java, rust, typescript, javascript`

#### The `GoToImplementationElseDeclaration` subcommand

Looks up the symbol under the cursor and jumps to its implementation if one,
else jump to its declaration. If there are multiple implementations, instead
provides a list of implementations to choose from.

Supported in filetypes: `cs`

#### The `GoToType` subcommand

Looks up the symbol under the cursor and jumps to the definition of its type
e.g. if the symbol is an object, go to the definition of its class.

Supported in filetypes: `go, java, javascript, typescript`

#### The `GoToDocumentOutline` subcommand

Provides a list of symbols in current document, in the quickfix list. See also
[interactive symbol search](#symbol-search).

Supported in filetypes: `c, cpp, objc, objcpp, cuda, go, java, rust`

#### The `GoToCallers` and `GoToCallees` subcommands

Populate the quickfix list with the callers, or callees respectively, of the
function associated with the current cursor position. The semantics of this
differ depending on the filetype and language server.

Only supported for LSP servers which provide the `callHierarchyProvider`
capability.

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
go, python, typescript, rust`

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

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, go, java, javascript,
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

Where available, attempts to make changes to the buffer to correct diagnostics,
or perform refactoring, on the current line or selection. Where multiple
suggestions are available (such as when there are multiple ways to resolve a
given warning, or where multiple diagnostics are reported for the current line,
or multiple refactoring tweaks are available), the options are presented and
one can be selected.

Completers which provide diagnostics may also provide trivial modifications to
the source in order to correct the diagnostic. Examples include syntax errors
such as missing trailing semi-colons, spurious characters, or other errors which
the semantic engine can deterministically suggest corrections. A small demo
presenting how diagnostics can be fixed with clangd:

![YcmCompleter-FixIt-OnDiagnostic](https://user-images.githubusercontent.com/17928698/206855014-9131a49b-87e8-4ed4-8d91-f2fe7808a0b9.gif)

Completers (LSPs) may also provide refactoring tweaks, which may be available
even when no diagnostic is presented for the current line. These include
function extraction, variable extraction, `switch` population, constructor
generation, ... The tweaks work for a selection as well. Consult your LSP for
available refactorings. A demonstration of refactoring capabilities with clangd:

![YouCompleter-FixIt-Refactoring](https://user-images.githubusercontent.com/17928698/206855713-3588c8de-d0f5-4725-b65e-bc51110252cc.gif)

If no fix-it is available for the current line, or there is no diagnostic on the
current line, this command has no effect on the current buffer. If any
modifications are made, the number of changes made to the buffer is echo'd and
the user may use the editor's undo command to revert.

When a diagnostic is available, and `g:ycm_echo_current_diagnostic` is enabled,
then the text ` (FixIt)` is appended to the echo'd diagnostic when the
completer is able to add this indication. The text ` (FixIt available)` is
also appended to the diagnostic text in the output of the `:YcmDiags` command
for any diagnostics with available fix-its (where the completer can provide this
indication).

**NOTE:** Causes re-parsing of the current translation unit.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, go, java, javascript,
rust, typescript`

#### The `RefactorRename <new name>` subcommand

In supported file types, this command attempts to perform a semantic rename of
the identifier under the cursor. This includes renaming declarations,
definitions and usages of the identifier, or any other language-appropriate
action. The specific behavior is defined by the semantic engine in use.

Similar to `FixIt`, this command applies automatic modifications to your source
files. Rename operations may involve changes to multiple files, which may or may
not be open in Vim buffers at the time. YouCompleteMe handles all of this for
you. The behavior is described in [the following section](#multi-file-refactor).

Supported in filetypes: `c, cpp, objc, objcpp, cuda, java, javascript, python, typescript, rust, cs`

#### Python refactorings

The following additional commands are supported for python:

* `RefactorInline`
* `RefactorExtractVariable`
* `RefactorExtractFunction`

See the [jedi docs][jedi-refactor-doc] for what they do.

Supported in filetypes: `python`

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

Supported in filetypes: `c, cpp, objc, objcpp, cuda, java, javascript, go, typescript, rust, cs`

#### The `OrganizeImports` subcommand

This command removes unused imports and sorts imports in the current file. It
can also group imports from the same module in TypeScript and resolves imports
in Java.

Supported in filetypes: `java, javascript, typescript`

### Miscellaneous Commands

These commands are for general administration, rather than IDE-like features.
They cover things like the semantic engine server instance and compilation
flags.

#### The `ExecuteCommand <args>` subcommand

Some LSP completers (currently only Java completers) support executing
server specific commands. Consult the [jdt.ls][] documentation to find out
what commands are supported and which arguments are expected.

The support for `ExecuteCommand` was implemented to support plugins like
[Vimspector][] to debug java, but isn't limited to that specific use case.

#### The `RestartServer` subcommand

Restarts the downstream semantic engine server for those semantic engines that
work as separate servers that YCM talks to.

Supported in filetypes: `c, cpp, objc, objcpp, cuda, cs, go, java, javascript, rust, typescript`

#### The `ReloadSolution` subcommand

Instruct the Omnisharp-Roslyn server to clear its cache and reload all files
from disk.  This is useful when files are added, removed, or renamed in the
solution, files are changed outside of Vim, or whenever Omnisharp-Roslyn cache
is out-of-sync.

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

### The `youcompleteme#GetCommandResponse( ... )` function

Run a [completer subcommand](#ycmcompleter-subcommands) and return the result as
a string. This can be useful for example to display the `GetGoc` output in a
popup window, e.g.:

```viml
let s:ycm_hover_popup = -1
function s:Hover()
  let response = youcompleteme#GetCommandResponse( 'GetDoc' )
  if response == ''
    return
  endif

  call popup_hide( s:ycm_hover_popup )
  let s:ycm_hover_popup = popup_atcursor( balloon_split( response ), {} )
endfunction

" CursorHold triggers in normal mode after a delay
autocmd CursorHold * call s:Hover()
" Or, if you prefer, a mapping:
nnoremap <silent> <leader>D :call <SID>Hover()<CR>
```

**NOTE**: This is only an example, for real hover support, see
[`g:ycm_auto_hover`](#the-gycm_auto_hover-option).

If the completer subcommand result is not a string (for example, it's a FixIt or
a Location), or if the completer subcommand raises an error, an empty string is
returned, so that calling code does not have to check for complex error
conditions.

The arguments to the function are the same as the arguments to the
`:YcmCompleter` ex command, e.g. the name of the subcommand, followed by any
additional subcommand arguments. As with the `YcmCompleter` command, if the
first argument is `ft=<filetype>` the request is targeted at the specified
filetype completer. This is an advanced usage and not necessary in most cases.

NOTE: The request is run synchronously and blocks Vim until the response is
received, so we do not recommend running this as part of an autocommand that
triggers frequently.

### The `youcompleteme#GetCommandResponseAsync( callback, ... )` function

This works exactly like `youcompleteme#GetCommandResponse`, except that instead
of returning the result, you supply a `callback` argument. This argument must be
a `FuncRef` to a function taking a single argument `response`. This callback
will be called with the command response at some point later, or immediately.

As with `youcompleteme#GetCommandResponse()`, this function will call the
callback with `''` (an empty string) if the request is not sent, or if there was
some sort of error.

Here's an example that's similar to the one above:

```viml

let s:ycm_hover_popup = -1
function! s:ShowDataPopup( response ) abort
  if response == ''
    return
  endif

  call popup_hide( s:ycm_hover_popup )
  let s:ycm_hover_popup = popup_atcursor( balloon_split( response ), {} )
endfunction

function! s:GetData() abort
  call youcompleteme#GetCommandResponseAsync(
    \ function( 's:ShowDataPopup' ),
    \ 'GetDoc' )
endfunction

autocommand CursorHold * call s:GetData()
```

Again, see [`g:ycm_auto_hover`](#the-gycm_auto_hover-option) for proper hover
support.

**NOTE**: The callback may be called immediately, in the stack frame that called
this function.

**NOTE**: Only one command request can be outstanding at once. Attempting to
request a second responses while the first is outstanding will result in the
second callback being immediately called with `''`.

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

### The `g:ycm_max_num_candidates_to_detail` option

Some completion engines require completion candidates to be 'resolved' in order
to get detailed info such as inline documentation, method signatures etc.  This
information is displayed by YCM in the preview window, or if `completeopt`
contains `popup`, in the info popup next to the completion menu.

By default, if the info popup is in use, and there are more than 10 candidates,
YCM will defer resolving candidates until they are selected in the completion
menu.  Otherwise, YCM must resolve the details upfront, which can be costly.

If neither `popup` nor `preview` are in `completeopt`, YCM disables resolving
altogether as the information would not be displayed.

This setting can be used to override these defaults and  controls the number of
completion candidates that should be resolved upfront. Typically users do not
need to change this, as YCM will work out an appropriate value based on your
`completeopt` and `g:ycm_add_preview_to_completeopt` settings. However, you may
override this calculation by setting this value to a number:

* `-1` - Resolve all candidates up front
* `0` - Never resolve any candidates up front.
* `> 0` - Resolve up to this many candidates up front. If the number of
  candidates is greater than this value, no candidates are resolved.

In the later two cases, if `completeopt` contains `popup`, then candidates are
resolved on demand asynchronously.

Default:

* `0` if neither `popup` nor `preview` are in `completeopt`.
* `10` if `popup` is in completeopt.
* `-1` if `preview` is in completeopt.

Example:

```viml
let g:ycm_max_num_candidates_to_detail = 0
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

When `g:ycm_auto_trigger` is `0`, YCM sets the `completefunc`, so that you can
manually trigger normal completion using `C-x C-u`.

If you want to map something else to trigger completion, such as `C-d``,
then you can map it to `<plug>(YCMComplete)`. For example:

```viml
let g:ycm_auto_trigger = 0
imap <c-d> <plug>(YCMComplete)
```

NOTE: It's not possible to map one of the keys in
`g:ycm_key_list_select_completion` (or similar) to `<plug>(YCMComplete)`. In
practice that means that you can't use `<Tab>` for this.

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

** Completion in buffers with no filetype **

There is one exception to the above rule. YCM supports completion in buffers
with no filetype set, but this must be _explicitly_ whitelisted. To identify
buffers with no filetype, we use the `ycm_nofiletype` pseudo-filetype. To enable
completion in buffers with no filetype, set:

```viml
let g:ycm_filetype_whitelist = {
  \ '*': 1,
  \ 'ycm_nofiletype': 1
  \ }
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
      \ 'leaderf': 1,
      \ 'mail': 1
      \}
```

In addition, `ycm_nofiletype` (representing buffers with no filetype set)
is blacklisted if `ycm_nofiletype` is not _explicitly_ whitelisted (using
`g:ycm_filetype_whitelist`).

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

When this option is set to 1, YCM will echo the text of the diagnostic present
on the current line when you move your cursor to that line. If a `FixIt` is
available for the current diagnostic, then ` (FixIt)` is appended.

If you have a Vim that supports virtual text, you can set this option
to the string `virtual-text`, and the diagnostic will be displayed inline with
the text, right aligned in the window and wrapping to the next line if there is
not enough space, for example:

![Virtual text diagnostic demo][diagnostic-echo-virtual-text1]

![Virtual text diagnostic demo][diagnostic-echo-virtual-text2]

**NOTE**: It's _strongly_ recommended to also set
`g:ycm_update_diagnostics_in_insert_mode` to `0` when using `virtual-text` for
diagnostics. This is due to the increased amount distraction provided by
drawing diagnostics next to your input position.

This option is part of the Syntastic compatibility layer; if the option is not
set, YCM will fall back to the value of the `g:syntastic_echo_current_error`
option before using this option's default.

Default: `1`

Valid values:

* `0` - disabled
* `1` - echo diagnostic to the command area
* `'virtual-text'` - display the dignostic to the right of the line in the
  window using virtual text

```viml
let g:ycm_echo_current_diagnostic = 1
" Or, when you have Vim supporting virtual text
let g:ycm_echo_current_diagnostic = 'virtual-text'
```

### The `g:ycm_auto_hover` option

This option controls whether or not YCM shows documentation in a popup at the
cursor location after a short delay. Only supported in Vim.

When this option is set to `'CursorHold'`, the popup is displayed on the
`CursorHold` autocommand. See `:help CursorHold` for the details, but this means
that it is displayed after `updatetime` milliseconds.  When set to an empty
string, the popup is not automatically displayed.

In addition to this setting, there is the `<plug>(YCMHover)` mapping, which can
be used to manually trigger or hide the popup (it works like a toggle).
For example:

```viml
nmap <leader>D <plug>(YCMHover)
```

After dismissing the popup with this mapping, it will not be automatically
triggered again until the cursor is moved (i.e. `CursorMoved` autocommand).

The displayed documentation depends on what the completer for the current
language supports. It's selected heuristically in this order of preference:

1. `GetHover` with `markdown` syntax
2. `GetDoc` with no syntax
3. `GetType` with the syntax of the current file. 

You can customise this by manually setting up `b:ycm_hover` to your liking. This
buffer-local variable can be set to a dictionary with the following keys:

* `command`: The YCM completer subcommand which should be run on hover
* `syntax`: The syntax to use (as in `set syntax=`) in the popup window for
  highlighting.

For example, to use C/C++ syntax highlighting in the popup for C-family
languages, add something like this to your vimrc:

```viml
augroup MyYCMCustom
  autocmd!
  autocmd FileType c,cpp let b:ycm_hover = {
    \ 'command': 'GetDoc',
    \ 'syntax': &filetype
    \ }
augroup END
```

Default: `'CursorHold'`

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
when the regex (treated as case-insensitive) is found anywhere in the diagnostic
text (`re.search`, not `re.match`)
- "level": Accepts a string level, either "warning" or "error." This type
matches when the diagnostic has the same level, that is,
specifying `level: "error"` will remove **all** errors from the diagnostics.

**NOTE:** The regex syntax is **NOT** Vim's, it's [Python's][python-re].

Default: `{}`

The following example will do, for java filetype only:
- Remove **all** error level diagnostics, and,
- Also remove anything that contains `ta<something>co`

```viml
let g:ycm_filter_diagnostics = {
  \ "java": {
  \      "regex": [ "ta.+co", ... ],
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

Note: if YCM's errors aren't visible, it might be that YCM is updating an older location list. See `:help :lhistory` and `:lolder`.

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

When set to `1`, the OmniSharp-Roslyn server will be automatically started
(once per Vim session) when you open a C# file.

Default: `1`

```viml
let g:ycm_auto_start_csharp_server = 1
```

### The `g:ycm_auto_stop_csharp_server` option

When set to `1`, the OmniSharp-Roslyn server will be automatically stopped upon
closing Vim.

Default: `1`

```viml
let g:ycm_auto_stop_csharp_server = 1
```

### The `g:ycm_csharp_server_port` option

When g:ycm_auto_start_csharp_server is set to `1`, specifies the port for
the OmniSharp-Roslyn server to listen on. When set to `0` uses an unused port provided
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
already has `preview` set, there will be no effect. Alternatively, when set to
`popup` and your version of Vim supports popup windows (see `:help popup`), the
`popup` string will be used instead. You can see the current state of your
`completeopt` setting with `:set completeopt?` (yes, the question mark is
important).

When `preview` is present in `completeopt`, YCM will use the `preview` window at
the top of the file to store detailed information about the current completion
candidate (but only if the candidate came from the semantic engine). For
instance, it would show the full function prototype and all the function
overloads in the window if the current completion is a function name.

When `popup` is present in `completeopt`, YCM will instead use a `popup`
window to the side of the completion popup for storing detailed information
about the current completion candidate. In addition, YCM may truncate the
detailed completion information in order to give the popup sufficient room
to display that detailed information.

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
after typing characters appropriate for the language, such as `.`, `->`, `::`,
etc. in insert mode (if semantic completion support has been compiled in). This
key mapping can be used to trigger semantic completion anywhere. Useful for
searching for top-level functions and classes.

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

If you prefer the detailed diagnostic to be shown in a popup, then
`let g:ycm_show_detailed_diag_in_popup=1`.

Default: `<leader>d`

```viml
let g:ycm_key_detailed_diagnostics = '<leader>d'
```

### The `g:ycm_show_detailed_diag_in_popup` option

Makes `:YcmShowDetailedDiagnostic` always show in a popup rather than echoing to
the command line.

Default: 0

```viml
let g:ycm_show_detailed_diag_in_popup = 0
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

### The `g:ycm_language_server` option

This option lets YCM use an arbitrary Language Server Protocol (LSP) server, not
unlike many other completion systems.  The officially supported completers are
favoured over custom LSP ones, so overriding an existing completer means first
making sure YCM won't choose that existing completer in the first place.

A simple working example of this option can be found in the section called
["Semantic Completion for Other Languages"](#semantic-completion-for-other-languages).

Many working examples can be found in the YCM [lsp-examples][] repo.

Default: `[]`

```viml
let g:ycm_language_server = []
```

### The `g:ycm_disable_signature_help` option

This option allows you to disable all signature help for all completion engines.
There is no way to disable it per-completer. This option is _reserved_, meaning
that while signature help support remains experimental, its values and meaning
may change and it may be removed in a future version.

Default: `0`

```viml
" Disable signature help
let g:ycm_disable_signature_help = 1
```

### The `g:ycm_gopls_binary_path` option

In case the system-wide `gopls` binary is newer than the bundled one, setting
this option to the path of the system-wide `gopls` would make YCM use that one
instead.

If the path is just `gopls`, YCM will search in `$PATH`.


### The `g:ycm_gopls_args` option

Similar to [the `g:ycm_clangd_args`](#the-gycm-clangd-args), this option allows
passing additional flags to the `gopls` command line.

Default: `[]`

```viml
let g:ycm_gopls_args = []
```


### The `g:ycm_rls_binary_path` and `g:ycm_rustc_binary_path` options

YCM no longer uses RLS for rust, and these options are therefore no longer
supported.

To use a custom rust-analyzer, see `g:ycm_rust_toolchain_root`.

### The `g:ycm_rust_toolchain_root` option

Optionally specify the path to a custom rust toolchain including at least a
supported version of `rust-analyzer`.


### The `g:ycm_tsserver_binary_path` option

Similar to [the `gopls` path](#the-gycm-gopls-binaty-path), this option
tells YCM where is the TSServer executable located.

### The `g:ycm_roslyn_binary_path` option

Similar to [the `gopls` path](#the-gycm-gopls-binaty-path), this option
tells YCM where is the Omnisharp-Roslyn executable located.

### The `g:ycm_update_diagnostics_in_insert_mode` option

With async diagnostics, LSP servers might send new diagnostics mid-typing.
If seeing these new diagnostics while typing is not desired, this option can
be set to 0.

When this option is set to `0`, diagnostic signs, virtual text and highlights
are cleared when entering insert mode and replaced when leaving insert mode.
This reduces visual noise while editing.

In addition, this option is recommended when `g:ycm_echo_current_diagnostic` is
set to `virtual-text` as it prevents updating the virtual text while you are
typing.

Default: `1`

```viml
let g:ycm_update_diagnostics_in_insert_mode = 1
```

FAQ
---

The FAQ section has been moved to the [wiki][wiki-faq].

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
<https://ycm-core.github.io/YouCompleteMe/>.

The author's homepage is <https://val.markovic.io>.

Please do **NOT** go to #vim, reddit, or stack overflow for support. Please
contact the YouCompleteMe maintainers directly using the [contact
details](#contact).

License
-------

This software is licensed under the [GPL v3 license][gpl].
© 2015-2018 YouCompleteMe contributors

Sponsorship
-----------

If you like YCM so much that you're wiling to part with your hard-earned cash, please consider donating to one of the following charities, which are meaningful to the current maintainers (in no particular order):

* [Greyhound Rescue Wales](https://greyhoundrescuewales.co.uk)
* [Be Humane](https://www.budihuman.rs/en)
* [Cancer Research UK](https://www.cancerresearchuk.org)
* [ICCF Holland](https://iccf.nl)
* Any charity of your choosing.

Please note: The YCM maintainers do not specifically endorse nor necessarily have any relationship with the above charities. Disclosure: It is noted that one key maintainer is family with Trustees of Greyhound Rescue Wales.


[ycmd]: https://github.com/ycm-core/ycmd
[Clang]: https://clang.llvm.org/
[vundle]: https://github.com/VundleVim/Vundle.vim#about
[brew]: https://brew.sh
[cmake-download]: https://cmake.org/download/
[macvim]: https://macvim-dev.github.io/macvim/
[vimrc]: https://vimhelp.appspot.com/starting.txt.html#vimrc
[gpl]: https://www.gnu.org/copyleft/gpl.html
[vim]: https://www.vim.org/
[syntastic]: https://github.com/scrooloose/syntastic
[lightline]: https://github.com/itchyny/lightline.vim
[ycm_flags_example]: https://github.com/ycm-core/YouCompleteMe/blob/master/.ycm_extra_conf.py
[ycmd_flags_example]: https://raw.githubusercontent.com/ycm-core/ycmd/66030cd94299114ae316796f3cad181cac8a007c/.ycm_extra_conf.py
[compdb]: https://clang.llvm.org/docs/JSONCompilationDatabase.html
[subsequence]: https://en.wikipedia.org/wiki/Subsequence
[listtoggle]: https://github.com/Valloric/ListToggle
[vim-build]: https://github.com/ycm-core/YouCompleteMe/wiki/Building-Vim-from-source
[tracker]: https://github.com/ycm-core/YouCompleteMe/issues?state=open
[completer-api]: https://github.com/ycm-core/ycmd/blob/master/ycmd/completers/completer.py
[eclim]: http://eclim.org/
[jedi]: https://github.com/davidhalter/jedi
[ultisnips]: https://github.com/SirVer/ultisnips/blob/master/doc/UltiSnips.txt
[ctags-format]: http://ctags.sourceforge.net/FORMAT
[ycm-users]: https://groups.google.com/forum/?hl=en#!forum/ycm-users
[omnisharp-roslyn]: https://github.com/OmniSharp/omnisharp-roslyn
[python-re]: https://docs.python.org/2/library/re.html#regular-expression-syntax
[Bear]: https://github.com/rizsotto/Bear
[ygen]: https://github.com/rdnetto/YCM-Generator
[Gopls]: https://github.com/golang/go/wiki/gopls
[gopls-preferences]: https://github.com/golang/tools/blob/master/internal/lsp/server.go
[TSServer]: https://github.com/Microsoft/TypeScript/tree/master/src/server
[jsconfig.json]: https://code.visualstudio.com/docs/languages/jsconfig
[tsconfig.json]: https://www.typescriptlang.org/docs/handbook/tsconfig-json.html
[vim-win-download]: https://github.com/vim/vim-win32-installer/releases
[python-win-download]: https://www.python.org/downloads/windows/
[visual-studio-download]: https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16
[mono-install-macos]: https://www.mono-project.com/download/stable/
[mono-install-linux]: https://www.mono-project.com/download/stable/#download-lin
[go-install]: https://golang.org/doc/install
[npm-install]: https://docs.npmjs.com/getting-started/installing-node#1-install-nodejs--npm
[tern-instructions]: https://github.com/ycm-core/YouCompleteMe/wiki/JavaScript-Semantic-Completion-through-Tern
[libclang-instructions]: https://github.com/ycm-core/YouCompleteMe/wiki/C-family-Semantic-Completion-through-libclang
[Tern]: https://ternjs.net
[rls]: https://github.com/rust-lang/rls
[rust-analyzer]: https://rust-analyzer.github.io
[rust-src]: https://www.rust-lang.org/downloads.html
[add-msbuild-to-path]: https://stackoverflow.com/questions/6319274/how-do-i-run-msbuild-from-the-command-line-using-windows-sdk-7-1
[ccoc]: https://github.com/ycm-core/YouCompleteMe/blob/master/CODE_OF_CONDUCT.md
[gitter]: https://gitter.im/Valloric/YouCompleteMe
[ninja-compdb]: https://ninja-build.org/manual.html
[++enc]: http://vimdoc.sourceforge.net/htmldoc/editing.html#++enc
[contributing-md]: https://github.com/ycm-core/YouCompleteMe/blob/master/CONTRIBUTING.md
[jdt.ls]: https://github.com/eclipse/eclipse.jdt.ls
[jdk-install]: https://adoptium.net/en-GB/temurin/releases
[mvn-project]: https://maven.apache.org/guides/getting-started/maven-in-five-minutes.html
[eclipse-project]: https://help.eclipse.org/oxygen/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Freference%2Fmisc%2Fproject_description_file.html
[gradle-project]: https://docs.gradle.org/current/userguide/tutorial_java_projects.html
[eclipse-dot-project]: https://help.eclipse.org/oxygen/index.jsp?topic=%2Forg.eclipse.platform.doc.isv%2Freference%2Fmisc%2Fproject_description_file.html
[eclipse-dot-classpath]: https://help.eclipse.org/mars/index.jsp?topic=%2Forg.eclipse.jdt.doc.isv%2Freference%2Fapi%2Forg%2Feclipse%2Fjdt%2Fcore%2FIClasspathEntry.html
[ycmd-eclipse-project]: https://github.com/ycm-core/ycmd/tree/3602f38ef7a762fc765afd75e562aec9a134711e/ycmd/tests/java/testdata/simple_eclipse_project
[ycmd-mvn-pom-xml]: https://github.com/ycm-core/ycmd/blob/3602f38ef7a762fc765afd75e562aec9a134711e/ycmd/tests/java/testdata/simple_maven_project/pom.xml
[ycmd-gradle-project]: https://github.com/ycm-core/ycmd/tree/3602f38ef7a762fc765afd75e562aec9a134711e/ycmd/tests/java/testdata/simple_gradle_project
[jdtls-preferences]: https://github.com/eclipse/eclipse.jdt.ls/blob/master/org.eclipse.jdt.ls.core/src/org/eclipse/jdt/ls/core/internal/preferences/Preferences.java
[diacritic]: https://www.unicode.org/glossary/#diacritic
[clangd]: https://clang.llvm.org/extra/clangd.html
[vimspector]: https://github.com/puremourning/vimspector
[compiledb]: https://pypi.org/project/compiledb/
[signature-help-pr]: https://github.com/ycm-core/ycmd/pull/1255
[wiki-faq]: https://github.com/ycm-core/YouCompleteMe/wiki/FAQ
[wiki-full-install]: https://github.com/ycm-core/YouCompleteMe/wiki/Full-Installation-Guide
[wiki-troubleshooting]: https://github.com/ycm-core/YouCompleteMe/wiki/Troubleshooting-steps-for-ycmd-server-SHUT-DOWN
[lsp-examples]: https://github.com/ycm-core/lsp-examples
[diagnostic-echo-virtual-text1]: https://user-images.githubusercontent.com/10584846/185707973-39703699-0263-47d3-82ac-639d52259bea.png
[diagnostic-echo-virtual-text2]: https://user-images.githubusercontent.com/10584846/185707993-14ff5fd7-c082-4e5a-b825-f1364e619b6a.png
[jedi-refactor-doc]: https://jedi.readthedocs.io/en/latest/docs/api.html#jedi.Script.extract_variable
