YouCompleteMe: a code-completion engine for Vim
===============================================

YouCompleteMe is a fast, as-you-type, fuzzy-search code completion engine for
[Vim][]. It has two completion engines: an identifier-based engine that works
with every programing language and a semantic, [Clang][]-based engine that
provides semantic code completion for C/C++/Objective-C/Objective-C++ (from now
on referred to as "the C-family languages").


Mac OS X super-quick installation
---------------------------------

Please refer to the full Installation Guide below; the following commands are
provided on a best-effort basis and may not work for you.

Install the latest version of [MacVim][]. Yes, MacVim. And yes, the _latest_.

Install YouCompleteMe with [Vundle][].

Install CMake. Preferably with [Homebrew][brew], but here's the [stand-alone
CMake installer][cmake-download].

_If_ you care about semantic completion for C-family languages, type in the
following commands in the console. If you don't, **skip this step**.

    cd ~
    mkdir ycm_temp
    cd ycm_temp
    curl -O http://llvm.org/releases/3.2/clang+llvm-3.2-x86_64-apple-darwin11.tar.gz
    tar -zxvf clang+llvm-3.2-x86_64-apple-darwin11.tar.gz
    cp clang+llvm-3.2-x86_64-apple-darwin11/lib/libclang.dylib ~/.vim/bundle/YouCompleteMe/python

Compiling YCM **with** semantic support for C-family languages (previous step
required):

    cd ~
    makedir ycm_build
    cd ycm_build
    cmake -G "Unix Makefiles" -DPATH_TO_LLVM_ROOT=~/ycm_temp/clang+llvm-3.2-x86_64-apple-darwin11 . ~/.vim/bundle/YouCompleteMe/cpp
    make

Compiling YCM **without** semantic support for C-family languages:

    cd ~
    makedir ycm_build
    cd ycm_build
    cmake -G "Unix Makefiles" . ~/.vim/bundle/YouCompleteMe/cpp
    make

That's it. You're done. Refer to the User Guide section on how to use YCM. Don't
forget that if you want the C-family semantic completion engine to work, you
will need to provide the compilation flags for your project to YCM. It's all in
the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

Ubuntu Linux x64 super-quick installation
-----------------------------------------

Please refer to the full Installation Guide below; the following commands are
provided on a best-effort basis and may not work for you.

Make sure you have Vim 7.3.584 with python2 support. At the time of writing, the
version of Vim shipping with Ubuntu is too old. You may need to compile Vim from
source.

Install YouCompleteMe with [Vundle][].

Install CMake. `sudo apt-get instal cmake`

_If_ you care about semantic completion for C-family languages, type in the
following commands in the console. If you don't, **skip this step**.

    cd ~
    mkdir ycm_temp
    cd ycm_temp
    curl -O http://llvm.org/releases/3.2/clang+llvm-3.2-x86_64-linux-ubuntu-12.04.tar.gz
    tar -zxvf clang+llvm-3.2-x86_64-linux-ubuntu-12.04.tar.gz
    cp clang+llvm-3.2-x86_64-linux-ubuntu-12.04/lib/libclang.so ~/.vim/bundle/YouCompleteMe/python

Compiling YCM **with** semantic support for C-family languages (previous step
required):

    cd ~
    mkdir ycm_build
    cd ycm_build
    cmake -G "Unix Makefiles" -DPATH_TO_LLVM_ROOT=~/ycm_temp/clang+llvm-3.2-x86_64-linux-ubuntu-12.04 . ~/.vim/bundle/YouCompleteMe/cpp
    make

Compiling YCM **without** semantic support for C-family languages:

    cd ~
    mkdir ycm_build
    cd ycm_build
    cmake -G "Unix Makefiles" . ~/.vim/bundle/YouCompleteMe/cpp
    make

That's it. You're done. Refer to the User Guide section on how to use YCM. Don't
forget that if you want the C-family semantic completion engine to work, you
will need to provide the compilation flags for your project to YCM. It's all in
the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.


Full Installation Guide
-----------------------

These are the steps necessary to get YCM working on a Unix OS like Linux or
Mac OS X. My apologies to Windows users, but I don't have a guide for them. The
code is platform agnostic, so if everything is configured correctly, YCM
_should_ work on Windows without issues (but as of writing, it's untested on
that platform).

Please follow the instructions carefully:

1.  **Ensure that your version of Vim is _at least_ 7.3.584 _and_ that it has
    support for python2 scripting**.

    Inside Vim, type `:version`. Look at the first two to three lines of output;
    it should say `Vi IMproved 7.3` and then below that, `Included patches:
    1-X`, where X will be some number. That number needs to be 584 or higher.

    After you have made sure that you have Vim 7.3.584+, type the following in
    Vim: `:has('python')`. The output should be 1. If it's 0, then get a version
    of Vim with Python support.

2.  **Install YCM** with [Vundle][] (or [Pathogen][], but Vundle is a better
    idea). With Vundle, this would mean adding a `Bundle
    'Valloric/YouCompleteMe'` line to your [vimrc][].

3.  [Complete this step ONLY if you care about semantic completion support for
    C-family languages. Otherwise it's not neccessary.]

    **Download the latest version of `libclang`**. Clang is an open-source
    compiler that can compile C/C++/Objective-C/Objective-C++. The `libclang`
    library it provides is used to power the YCM semantic completion engine for
    those languages. YCM needs libclang version 3.2 or higher.

    You can use the system libclang _only if you are sure it is version 3.2 or
    higher_, otherwise don't. Even if it is, I recommend using the [official
    binaries from llvm.org][clang-download] if at all possible. Make sure you
    download the correct archive file for your OS.

4.  **Compile the `ycm_core` plugin plugin** (ha!) that YCM needs. This is C++
    engine that YCM uses to get fast completions.

    You will need to have `cmake` installed in order to generate the required
    makefiles. Linux users can install cmake with their package manager (`sudo
    apt-get install cmake` for Ubuntu) whereas other users can [download and
    install][cmake-download] cmake from its project site. Mac users can also get
    it through [Homebrew][brew] with `brew install cmake`.

    Here we'll assume you installed YCM with Vundle. That means that the
    top-level YCM directory is in `~/.vim/bundle/YouCompleteMe`.

    We'll create a new folder where build files will be placed. Run the
    following:

        cd ~
        mkdir ycm_build
        cd ycm_build

    Now we need to generate the makefiles. If you DON'T care about semantic
    support for C-family languages, run the following command in the `ycm_build`
    directory: `cmake -G "Unix Makefiles" . ~/.vim/bundle/YouCompleteMe/cpp`

    If you DO care about semantic support for C-family languages, then your
    `cmake` call will be a bit more complicated.  We'll assume you downloaded a
    binary distribution of LLVM+Clang from llvm.org in step 3 and that you
    extracted the archive file to folder `~/ycm_temp/llvm_root_dir` (with `bin`,
    `lib`, `include` etc. folders right inside that folder). With that in mind,
    run the following command in the `ycm_build` directory: `cmake -G "Unix Makefiles" -DPATH_TO_LLVM_ROOT=~/ycm_temp/llvm_root_dir . ~/.vim/bundle/YouCompleteMe/cpp`

    Now that makefiles have been generated, simply run `make`.

    For those who want to use the system version of libclang, you would pass
    `-DUSE_SYSTEM_LIBCLANG=ON` to cmake _instead of_ the
    `-DPATH_TO_LLVM_ROOT=...` flag.

    You could also force the use of a custom libclang library with
    `-DEXTERNAL_LIBCLANG_PATH=/path/to/libclang.so` flag (the library would end
    with `.dylib` on a Mac). Again, this flag would be used _instead of_ the
    other flags.

5.  [Complete this step ONLY if you care about semantic completion support for
    C-family languages. Otherwise it's not neccessary.]

    **Copy the libclang library file into the `YouCompleteMe/python` folder.**
    The library file is `libclang.so` on Linux and `libclang.dylib` on Mac.

    We'll assume you downloaded a binary distribution of LLVM+Clang from
    llvm.org in step 3 and that you extracted the archive file to folder
    `~/ycm_temp/llvm_root_dir` (with `bin`, `lib`, `include` etc. folders right
    inside that folder).

    We'll also assume you installed YCM with Vundle. That means that the
    top-level YCM directory is in `~/.vim/bundle/YouCompleteMe`.

    On Linux, run: `cp ~/ycm_temp/llvm_root_dir/lib/libclang.so ~/.vim/bundle/YouCompleteMe/python`

    On Mac, run: `cp ~/ycm_temp/llvm_root_dir/lib/libclang.dylib ~/.vim/bundle/YouCompleteMe/python`

That's it. You're done. Refer to the User Guide section on how to use YCM. Don't
forget that if you want the C-family semantic completion engine to work, you
will need to provide the compilation flags for your project to YCM. It's all in
the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

User Guide
----------

TODO, still WIP

### General Usage

- If the offered completions are too broad, keep typing characters; YCM will
  continue refining the offered completions based on your input.
- Use the TAB key to accept a completion and continue pressing TAB to cycle
  through the completions. Use Ctrl+TAB to cycle backwards.

### Semantic Completion Engine Usage

- You can use Ctrl+Space to trigger the completion suggestions anywhere, even
  without a string prefix.  This is useful to see which top-level functions are
  available for use.
- You _really_ also want to install the latest version of the [Syntastic][] Vim
  plugin. It has support for YCM and together they will provide you with compile
  errors/warnings practically instantly and without saving the file.

YCM looks for a `.ycm_clang_options.py` file in the directory of the opened file
or in any directory above it in the hierarchy (recursively); when the file is
found, it is loaded (only once!) as a Python module. YCM calls a `FlagsForFile`
method in that module which should provide it with the information necessary to
compile the current file.

This system was designed this way so that the user can perform any arbitrary
sequence of operations to produce a list of compilation flags YCM should hand
to Clang.

[See YCM's own `.ycm_clang_options.py`][flags_example] for details on how this
works. You should be able to use it as a starting point. Hint: just replace the
strings in the `flags` variable with compilation flags necessary for your
project. That should be enough for 99% of projects.

Yes, [Clang's `CompilationDatabase` system][compdb] is also supported. Again, see the
above linked example file.

TODO: compile flags, include paths, ycm_clang_options, CompilationDatabase
support, how the search system works (subsequence match), extending the semantic
engine for other langs, using ListToggle

Options
-------

All options have reasonable defaults so if the plug-in works after installation
you don't need to change any options. These options can be configured in your
[vimrc script][vimrc] by including a line like this:

    let g:ycm_min_num_of_chars_for_completion = 1

Note that after changing an option in your [vimrc script] [vimrc] you have to
restart Vim for the changes to take effect.

### The `g:ycm_min_num_of_chars_for_completion` option

This option controls the number of characters the user needs to type before
completion suggestions are triggered. For example, if the option is set to `2`,
then when the user types a second alphanumeric character after a whitespace
character, completion suggestions will be triggered.

Default: `2`

    let g:ycm_min_num_of_chars_for_completion = 2

### The `g:ycm_filetypes_to_completely_ignore` option

This option controls for which Vim filetypes (see `:h filetype`) should YCM be
turned off. The option value should be a Vim dictionary with keys being filetype
strings (like `python`, `cpp` etc) and values being unimportant (the dictionary
is used like a hash set, meaning that only the keys matter). The listed
filetypes will be completely ignored by YCM, meaning that neither the
identifier-based completion engine nor the semantic engine will operate in files
of those filetypes.

You can get the filetype of the current file in Vim with `:set ft?`.

Default: `{notes: 1, markdown: 1, text: 1}`

    let g:ycm_filetypes_to_completely_ignore = {
          \ 'notes' : 1,
          \ 'markdown' : 1,
          \ 'text' : 1,
          \}

### The `g:ycm_filetype_specific_completion_to_disable` option

This option controls for which Vim filetypes (see `:h filetype`) should the YCM
semantic completion engine be turned off. The option value should be a Vim
dictionary with keys being filetype strings (like `python`, `cpp` etc) and
values being unimportant (the dictionary is used like a hash set, meaning that
only the keys matter). The listed filetypes will be ignored by the YCM semantic
completion engine, but the identifier-based completion engine will still trigger
in files of those filetypes.

Note that even if semantic completion is not turned off for a specific filetype,
you will not get semantic completion if the semantic engine does not support
that filetype. Currently, the semantic engine only supports the `c`, `cpp`,
`objc` and `objcpp` filetypes.

You can get the filetype of the current file in Vim with `:set ft?`.

Default: `{}`

    let g:ycm_filetype_specific_completion_to_disable = {}

### The `g:ycm_allow_changing_updatetime` option

When this option is set to `1`, YCM will change the `updatetime` Vim option to
`2000` (see `:h updatetime`). This may conflict with some other plugins you have
(but it's unlikely). The `updatetime` option is the number of milliseconds that
have to pass before Vim's `CursorHold` (see `:h CursorHold`) event fires. YCM
runs the completion engines' "file comprehension" systems in the background on
every such event; the identifier-based engine collects the identifiers whereas
the semantic engine compiles the file to build an AST.

The Vim default of `4000` for `updatetime` is a bit long, so YCM reduces
this. Set this option to `0` to force YCM to leave your `updatetime` setting
alone.

Default: `1`

    let g:ycm_allow_changing_updatetime = 1

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

    let g:ycm_add_preview_to_completeopt = 0

### The `g:ycm_autoclose_preview_window_after_completion` option

When this option is set to `1`, YCM will auto-close the `preview` window after
the user accepts the offered completion string. If there is no `preview` window
triggered because there is no `preview` string in `completeopt`, this option is
irrelevant. See the `g:ycm_add_preview_to_completeopt` option for more details.

Default: `0`

    let g:ycm_autoclose_preview_window_after_completion = 0

### The `g:ycm_max_diagnostics_to_display` option

This option controls the maximum number of diagnostics shown to the user when
errors or warnings are detected in the file. This option is only relevant if you
are using the semantic completion engine and have installed the version of the
Syntastic plugin that supports YCM.

Default: `30`

    let g:ycm_max_diagnostics_to_display = 30


FAQ
---

TODO

Contact
-------

If you have questions, bug reports, suggestions, etc. please use the [issue
tracker][tracker]. The latest version is available at
<http://valloric.github.com/YouCompleteMe/>.

The author's homepage is <http://val.markovic.io>.

License
-------

This software is licensed under the [GPL v3 license][gpl].
© 2012 Strahinja Val Markovic &lt;<val@markovic.io>&gt;.


[Clang]: http://clang.llvm.org/
[vundle]: https://github.com/gmarik/vundle#about
[pathogen]: https://github.com/tpope/vim-pathogen#pathogenvim
[clang-download]: http://llvm.org/releases/download.html#3.2
[brew]: http://mxcl.github.com/homebrew/
[cmake-download]: http://www.cmake.org/cmake/resources/software.html
[macvim]: http://code.google.com/p/macvim/#Download
[vimrc]: http://vimhelp.appspot.com/starting.txt.html#vimrc
[gpl]: http://www.gnu.org/copyleft/gpl.html
[vim]: http://www.vim.org/
[syntastic]: https://github.com/scrooloose/syntastic
[flags_example]: https://github.com/Valloric/YouCompleteMe/blob/master/cpp/ycm/.ycm_clang_options.py
[compdb]: http://clang.llvm.org/docs/JSONCompilationDatabase.html
