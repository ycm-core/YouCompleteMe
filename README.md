YouCompleteMe: a code-completion engine for Vim
===============================================

YouCompleteMe is a fast, as-you-type, fuzzy-search code completion engine for
[Vim][]. It has several completion engines: an identifier-based engine that
works with every programming language, a semantic, [Clang][]-based engine that
provides native semantic code completion for C/C++/Objective-C/Objective-C++
(from now on referred to as "the C-family languages") and an omnifunc-based
completer that uses data from Vim's omnicomplete system to provide semantic
completions for many other languages (Python, Ruby, PHP etc.).

![YouCompleteMe GIF demo](http://i.imgur.com/0OP4ood.gif)

Here's an explanation of what happens in the short GIF demo above.

First, realize that **no keyboard shortcuts had to be pressed** to get the list
of completion candidates at any point in the demo. The user just types and the
suggestions pop up by themselves. If the user doesn't find the completion
suggestions relevant and/or just wants to type, he can do so; the completion
engine will not interfere.

When the user sees a useful completion string being offered, he presses the TAB
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
current file and other files you visit and searches them when you type
(identifiers are put into per-filetype groups).

The demo also shows the semantic engine in use. When the user presses `.`, `->`
or `::` while typing in insert mode, the semantic engine is triggered (it can
also be triggered with a keyboard shortcut; see the rest of the docs).

The last thing that you can see in the demo is YCM's integration with
[Syntastic][] (the little red X that shows up in the left gutter) if you are
editing a C-family file. As Clang compiles your file and detects warnings or
errors, they will be piped to Syntastic for display. You don't need to save your
file or press any keyboard shortcut to trigger this, it "just happens" in the
background.

In essence, YCM obsoletes the following Vim plugins because it has all of their
features plus extra:

- clang_complete
- AutoComplPop
- Supertab
- neocomplcache

Mac OS X super-quick installation
---------------------------------

Please refer to the full Installation Guide below; the following commands are
provided on a best-effort basis and may not work for you.

Install the latest version of [MacVim][]. Yes, MacVim. And yes, the _latest_.

If you don't use the MacVim GUI, it is recommended to use the Vim binary that is
inside the MacVim.app package (`MacVim.app/Contents/MacOS/Vim`). To ensure it
works correctly copy the `mvim` script from the [MacVim][] download to your
local binary folder (for example `/usr/local/bin/mvim`) and then symlink it:

    ln -s /usr/local/bin/mvim vim

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library API has changed (happens rarely), YCM will
notify you to recompile it. You should then rerun the install process.

It's recommended that you have the latest Xcode installed along with the latest
Command Line Tools (that you install from within Xcode).

Install CMake. Preferably with [Homebrew][brew], but here's the [stand-alone
CMake installer][cmake-download].

_If_ you have installed a Homebrew Python and/or Homebrew MacVim, see the FAQ
for details.

Compiling YCM **with** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.sh --clang-completer

Compiling YCM **without** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.sh

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
version of Vim shipping with Ubuntu is too old. You may need to [compile Vim
from source][vim-build] (don't worry, it's easy).

Install YouCompleteMe with [Vundle][].

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library API has changed (happens rarely), YCM will
notify you to recompile it. You should then rerun the install process.

Install development tools and CMake: `sudo apt-get install build-essential cmake`

Make sure you have Python headers installed: `sudo apt-get install python-dev`.

Compiling YCM **with** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.sh --clang-completer

Compiling YCM **without** semantic support for C-family languages:

    cd ~/.vim/bundle/YouCompleteMe
    ./install.sh

That's it. You're done. Refer to the User Guide section on how to use YCM. Don't
forget that if you want the C-family semantic completion engine to work, you
will need to provide the compilation flags for your project to YCM. It's all in
the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

Windows Installation
--------------------

YCM has **no official support for Windows**, but that doesn't mean you can't get
it to work there. See the [Windows Installation Guide][win-wiki] wiki page. Feel
free to add to it.

Full Installation Guide
-----------------------

These are the steps necessary to get YCM working on a Unix OS like Linux or
Mac OS X. My apologies to Windows users, but I don't have a guide for them. The
code is platform agnostic, so if everything is configured correctly, YCM
_should_ work on Windows without issues (but as of writing, it's untested on
that platform).

See the FAQ if you have any issues.

**Remember:** YCM is a plugin with a compiled component. If you **update** YCM
using Vundle and the ycm_core library API has changed (happens rarely), YCM will
notify you to recompile it. You should then rerun the install process.

**Please follow the instructions carefully. Read EVERY WORD.**

1.  **Ensure that your version of Vim is _at least_ 7.3.584 _and_ that it has
    support for python2 scripting**.

    Inside Vim, type `:version`. Look at the first two to three lines of output;
    it should say `Vi IMproved 7.3` and then below that, `Included patches:
    1-X`, where X will be some number. That number needs to be 584 or higher.

    If your version of Vim is not recent enough, you may need to [compile Vim
    from source][vim-build] (don't worry, it's easy).

    After you have made sure that you have Vim 7.3.584+, type the following in
    Vim: `:echo has('python')`. The output should be 1. If it's 0, then get a
    version of Vim with Python support.

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

4.  **Compile the `ycm_core` plugin plugin** (ha!) that YCM needs. This is the
    C++ engine that YCM uses to get fast completions.

    You will need to have `cmake` installed in order to generate the required
    makefiles. Linux users can install cmake with their package manager (`sudo
    apt-get install cmake` for Ubuntu) whereas other users can [download and
    install][cmake-download] cmake from its project site. Mac users can also get
    it through [Homebrew][brew] with `brew install cmake`.

    You also need to make sure you have Python headers installed. On a
    Debian-like Linux distro, this would be `sudo apt-get install python-dev`.
    On Mac they should already be present.

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

    Now that makefiles have been generated, simply run `make ycm_core`.

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

    **DO NOT FORGET THIS STEP**. If you forget to copy over `libclang.so`
    version 3.2 into the `YouCompleteMe/python` folder then YCM _will not work_
    if you selected C-family support during YCM compilation.

That's it. You're done. Refer to the User Guide section on how to use YCM. Don't
forget that if you want the C-family semantic completion engine to work, you
will need to provide the compilation flags for your project to YCM. It's all in
the User Guide.

YCM comes with sane defaults for its options, but you still may want to take a
look at what's available for configuration. There are a few interesting options
that are conservatively turned off by default that you may want to turn on.

User Guide
----------

### General Usage

- If the offered completions are too broad, keep typing characters; YCM will
  continue refining the offered completions based on your input.
- Filtering is "smart-case" sensitive; if you are typing only lowercase letters,
  then it's case-insensitive. If your input involves uppercase letters, then
  it's case-sensitive. So "foo" matches "Foo" and "foo", but "Foo" matches "Foo"
  but not "foo".
- Use the TAB key to accept a completion and continue pressing TAB to cycle
  through the completions. Use Shift-TAB to cycle backwards. Note that if you're
  using console Vim (that is, not Gvim or MacVim) then it's likely that the
  Shift-TAB binding will not work because the console will not pass it to Vim.
  You can remap the keys; see the options section below.

### Completion string ranking

The subsequence filter removes any completions that do not match the input, but
then the sorting system kicks in. It's actually very complicated and uses lots
of factors, but suffice it to say that "word boundary" (WB) subsequence
character matches are "worth" more than non-WB matches. In effect, this means
given an input of "gua", the completion "getUserAccount" would be ranked higher
in the list than the "Fooguxa" completion (both of which are subsequence
matches). A word-boundary character are all capital characters, characters
preceded by an underscore and the first letter character in the completion
string.

### General Semantic Completion Engine Usage

- You can use Ctrl+Space to trigger the completion suggestions anywhere, even
  without a string prefix. This is useful to see which top-level functions are
  available for use.

### C-family Semantic Completion Engine Usage

- You _really_ also want to install the latest version of the [Syntastic][] Vim
  plugin. It has support for YCM and together they will provide you with compile
  errors/warnings practically instantly and without saving the file.

YCM looks for a `.ycm_extra_conf.py` file in the directory of the opened file or
in any directory above it in the hierarchy (recursively); when the file is
found, it is loaded (only once!) as a Python module. YCM calls a `FlagsForFile`
method in that module which should provide it with the information necessary to
compile the current file. You can also provide a path to a global
`.ycm_extra_conf.py` file, which will be used as a fallback. To prevent the
execution of malicious code from a file you didn't write YCM will ask you once
per `.ycm_extra_conf.py` if it is safe to load. This can be disabled and you can
white-/blacklist files. See the Options section for more details.

This system was designed this way so that the user can perform any arbitrary
sequence of operations to produce a list of compilation flags YCM should hand
to Clang.

[See YCM's own `.ycm_extra_conf.py`][flags_example] for details on how this
works. You should be able to use it as a starting point. Hint: just replace the
strings in the `flags` variable with compilation flags necessary for your
project. That should be enough for 99% of projects.

Yes, [Clang's `CompilationDatabase` system][compdb] is also supported. Again, see the
above linked example file.

If Clang encounters errors when compiling the header files that your file
includes, then it's probably going to take a long time to get completions.  When
the completion menu finally appears, it's going to have a large number of
unrelated completion strings (type/function names that are not actually
members). This is because Clang fails to build a precompiled preamble for your
file if there are any errors in the included headers and that preamble is key to
getting fast completions.

Call the `:YcmDiags` command to see if any errors or warnings were detected in
your file. Even better, use Syntastic.

### Syntastic integration

YCM has explicit support for [Syntastic][] (and vice-versa) if you compiled YCM
with Clang support; this means that any diagnostics (errors or warnings) that
Clang encounters while compiling your file will be fed back to Syntastic for
display.

YCM will recompile your file in the background `updatetime` (see `:h updatetime`
in Vim) milliseconds after you stop typing (to be specific, on `CursorHold` and
`CursorHoldI` Vim events). YCM will change your `updatetime` value to be `2000`
milliseconds (there's an option to tell it not to do this if you wish).

The new diagnostics (if any) will be fed back to Syntastic the next time you
press any key on the keyboard. So if you stop typing and just wait for the new
diagnostics to come in, that _will not work_. You need to press some key for the
GUI to update.

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

After the errors are displayed by Syntastic, it will display a short diagnostic
message when you move your cursor to the line with the error. You can get a
detailed diagnostic message with the `<leader>d` key mapping (can be changed in
the options) YCM provides when your cursor is on the line with the diagnostic.

You can also see the full diagnostic message for all the diagnostics in the
current file in Vim's `locationlist`, which can be opened with the `:lopen` and
`:lclose` commands. A good way to toggle the display of the `locationlist` with
a single key mapping is provided by another (very small) Vim plugin called
[ListToggle][] (which also makes it possible to change the height of the
`locationlist` window), also written by yours truly.

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

Commands
--------

### The `YcmForceCompileAndDiagnostics` command

Calling this command will force YCM to immediately recompile your file
and display any new diagnostics it encounters. Do note that recompilation with
this command may take a while and during this time the Vim GUI _will_ be
blocked.

You may want to map this command to a key; try putting `nnoremap <F5>
:YcmForceCompileAndDiagnostics<CR>` in your vimrc.

### The `YcmDiags` command

Calling this command will fill Vim's `locationlist` with errors or warnings if
any were detected in your file and then open it.

A better option would be to use Syntastic which will keep your `locationlist`
up to date automatically and will also show error/warning notifications in Vim's
gutter.

### The `YcmShowDetailedDiagnostic` command

This command shows the full diagnostic text when the user's cursor is on the
line with the diagnostic.

### The `YcmDebugInfo` command

This will print out various debug information for the current file. Useful to
see what compile commands will be used for the file if you're using the semantic
completion engine.

### The `YcmCompleter` command

This command can be used to invoke completer-specific commands.  If the first
argument is of the form `ft=...` the completer for that file type will be used
(for example `ft=cpp`), else the native completer of the current buffer will be
used.
Call `YcmCompleter` without further arguments for information about the
commands you can call for the selected completer.

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

### The `g:ycm_filetype_whitelist` option

This option controls for which Vim filetypes (see `:h filetype`) should YCM be
turned on. The option value should be a Vim dictionary with keys being filetype
strings (like `python`, `cpp` etc) and values being unimportant (the dictionary
is used like a hash set, meaning that only the keys matter).

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

Default: `{'*' : 1}`

    let g:ycm_filetype_whitelist = { '*': 1 }

### The `g:ycm_filetype_blacklist` option

This option controls for which Vim filetypes (see `:h filetype`) should YCM be
turned off. The option value should be a Vim dictionary with keys being filetype
strings (like `python`, `cpp` etc) and values being unimportant (the dictionary
is used like a hash set, meaning that only the keys matter).

See the `g:ycm_filetype_whitelist` option for more details on how this works.

Default: `{'notes': 1, 'markdown': 1, 'text': 1}`

    let g:ycm_filetype_blacklist = {
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
that filetype.

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

### The `g:ycm_complete_in_comments_and_strings` option

When this option is set to `1`, YCM will show the completion menu even when
typing inside strings and comments.

Default: `0`

    let g:ycm_complete_in_comments_and_strings = 0

### The `g:ycm_collect_identifiers_from_comments_and_strings` option

When this option is set to `1`, YCM's identifier completer will also collect
identifiers from strings and comments. Otherwise, the text in comments and
strings will be ignored.

Default: `0`

    let g:ycm_collect_identifiers_from_comments_and_strings = 0

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

### The `g:ycm_autoclose_preview_window_after_insertion` option

When this option is set to `1`, YCM will auto-close the `preview` window after
the user leaves insert mode. This option is irrelevant if
`g:ycm_autoclose_preview_window_after_completion` is set or if no `preview`
window is triggered. See the `g:ycm_add_preview_to_completeopt` option for more
details.

Default: `0`

    let g:ycm_autoclose_preview_window_after_insertion = 0

### The `g:ycm_max_diagnostics_to_display` option

This option controls the maximum number of diagnostics shown to the user when
errors or warnings are detected in the file. This option is only relevant if you
are using the semantic completion engine and have installed the version of the
Syntastic plugin that supports YCM.

Default: `30`

    let g:ycm_max_diagnostics_to_display = 30

### The `g:ycm_key_list_select_completion` option

This option controls the key mappings used to select the first completion
string.  Invoking any of them repeatedly cycles forward through the completion
list.

Some users like adding `<Enter>` to this list.

Default: `['<TAB>', '<Down>']`

    let g:ycm_key_list_select_completion = ['<TAB>', '<Down>']

### The `g:ycm_key_list_previous_completion` option

This option controls the key mappings used to select the previous completion
string. Invoking any of them repeatedly cycles backwards through the completion
list.

Note that one of the defaults is `<S-TAB>` which means Shift-TAB. That mapping
will probably only work in GUI Vim (Gvim or MacVim) and not in plain console Vim
because the terminal usually does not forward modifier key combinations to Vim.

Default: `['<S-TAB>', '<Up>']`

    let g:ycm_key_list_previous_completion = ['<S-TAB>', '<Up>']

### The `g:ycm_key_invoke_completion` option

This option controls the key mapping used to invoke the completion menu for
semantic completion. By default, semantic completion is trigged automatically
after typing `.`, `->` and `::` in insert mode (if semantic completion support
has been compiled in). This key mapping can be used to trigger semantic
completion anywhere. Useful for searching for top-level functions and classes.

Note that the default of `<C-Space>` means Ctrl-Space. Also note that the
default mapping will probably only work in GUI Vim (Gvim or MacVim) and not in
plain console Vim because the terminal usually does not forward modifier key
combinations to Vim.

Setting this option to an empty string will make sure no mapping is created.

Default: `<C-Space>`

    let g:ycm_key_invoke_completion = '<C-Space>'

### The `g:ycm_key_detailed_diagnostics` option

This option controls the key mapping used to show the full diagnostic text when
the user's cursor is on the line with the diagnostic. It basically calls
`:YcmShowDetailedDiagnostic`.

Setting this option to an empty string will make sure no mapping is created.

Default: `<leader>d`

    let g:ycm_key_detailed_diagnostics = '<leader>d'

### The `g:ycm_global_ycm_extra_conf` option

Normally, YCM searches for a '.ycm_extra_conf.py' file for compilation flags
(see the User Guide for more details on how this works). This option specifies
a fallback path to a config file which is used if no '.ycm_extra_conf.py' is
found.

You can place such a global file anywhere in your filesystem.

Default: `''`

    let g:ycm_global_ycm_extra_conf = ''

### The `g:ycm_confirm_extra_conf` option

When this option is set to `1` YCM will ask once per `.ycm_extra_conf.py` file
if it is safe to be loaded. This is to prevent execution of malicious code
from a `.ycm_extra_conf.py` file you didn't write.

Default: `1`

    let g:ycm_confirm_extra_conf = 1

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

    let g:ycm_extra_conf_globlist = ['~/dev/*','!~/*']

* The first rule will match everything contained in the `~/dev` directory so
  `.ycm_extra_conf.py` files from there will be loaded.
* The second rule will match everything in the home directory so a
  `.ycm_extra_conf.py` file from there won't be loaded.
* As the first rule takes precedence everything in the home directory excluding
  the `~/dev` directory will be blacklisted.

Default: `[]`

    let g:ycm_extra_conf_globlist = []

### The `g:ycm_semantic_triggers` option

This option controls the character-based triggers for the various semantic
completion engines. The option holds a dictionary of key-values, where the keys
are Vim's filetype strings delimited by commas and values are lists of strings,
where the strings are the triggers.

A "trigger" is a sequence of one or more characters that trigger semantic
completion when typed. For instance, C++ (`cpp` filetype) has `.` listed as a
trigger. So when the user types `foo.`, the semantic engine will trigger and
serve `foo`'s list of member functions and variables. Since C++ also has `->`
listed as a trigger, the same thing would happen when the user typed `foo->`.

Default: `[see next line]`

    let g:ycm_semantic_triggers =  {
      \   'c' : ['->', '.'],
      \   'objc' : ['->', '.'],
      \   'cpp,objcpp' : ['->', '.', '::'],
      \   'perl' : ['->'],
      \   'php' : ['->', '::'],
      \   'cs,java,javascript,d,vim,ruby,python,perl6,scala,vb,elixir,go' : ['.'],
      \   'lua' : ['.', ':'],
      \   'erlang' : [':'],
      \ }

FAQ
---

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
various debugging information, including the compile flags for the file if the
file is a C-family language file and you have compiled in Clang support.

### I cannot get the Syntastic integration to work

Try to update your version of Syntastic. At the time of writing (Jan 2013), the
YCM integration is very recent and it's likely that your version of Syntastic
does not have it.

### Sometimes it takes much longer to get semantic completions than normal

This means that libclang (which YCM uses for C-family semantic completion)
failed to pre-compile your file's preamble. In other words, there was an error
compiling some of the source code you pulled in through your header files. I
suggest calling the `:YcmDiags` command to see what they were (even better, have
Syntastic installed and call `:lopen`).

Bottom line, if libclang can't pre-compile your file's preamble because there
were errors in it, you're going to get slow completions because there's no AST
cache.

### Vim flickers every time I move the cursor or moving the cursor is slow

You probably have an old version of Syntastic installed. If you are using
Vundle, make sure that your bundle command is `Bundle 'scrooloose/syntastic'`
and **not** `Bundle 'Syntastic'`. The first command pulls in the latest version of
Syntastic from GitHub while the second one pulls in an old version from vim.org.

### YCM auto-inserts completion strings I don't want!

This means you probably have some mappings that interfere with YCM's internal
ones. Make sure you don't have something mapped to `<C-p>`, `<C-x>` or `<C-u>`
(in insert mode).

YCM _never_ selects something for you; it just shows you a menu and the user has
to explicitly select something. If something is being selected automatically,
this means there's a bug or a misconfiguration somewhere.

### I get a `E227: mapping already exists for <blah>` error when I start Vim

This means that YCM tried to set up a key mapping but failed because you already
had something mapped to that key combination. The `<blah>` part of the message
will tell you what was the key combination that failed.

Look in the options section and see if which of the default mappings conflict
with your own. Then change that option value to something else so that the
conflict goes away.

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

### I get `Vim: Caught deadly signal SEGV` on Vim startup

This can happen on some Linux distros. If you encounter this situation, run Vim
under `gdb`. You'll probably see something like this in the output when Vim
crashes:

```
undefined symbol: clang_CompileCommands_dispose
```

This means that Vim is trying to load a `libclang.so` that is too old. You need
at least a 3.2 libclang. Some distros ship with a system `libclang.so` that
identifies itself as 3.2 but is not; it was cut from the upstream sources before
the official 3.2 release and some API changes (like the addition of the
CompileCommands API) were added after their cut.

So just go through the installation guide and make sure you are using a correct
`libclang.so`. I recommend downloading prebuilt binaries from llvm.org.

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
current file and simple prefix-based fitering.

### Why does YCM demand such a recent version of Vim?

During YCM's development several show-stopper bugs where encountered in Vim.
Those needed to be fixed upstream (and were). A few months after those bugs were
fixed, Vim trunk landed the `pyeval()` function which improved YCM performance
even more since less time was spent serializing and deserializing data between
Vim and the embedded Python interpreter. A few critical bugfixes for `pyeval()`
landed in Vim 7.3.584 (and a few commits before that).

### I get annoying messages in Vim's status area when I type

If you're referring to the `User defined completion <bla bla> back at original`
and similar, then sadly there's no fix for those. Vim will emit them no matter
how hard I try to silence them.

You'll have to learn to ignore them. It's a shitty "solution", I know.

### Nasty bugs happen if I have the `vim-autoclose` plugin installed

Use the [delimitMate][] plugin instead. It does the same thing without
conflicting with YCM.


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
[flags_example]: https://github.com/Valloric/YouCompleteMe/blob/master/cpp/ycm/.ycm_extra_conf.py
[compdb]: http://clang.llvm.org/docs/JSONCompilationDatabase.html
[subsequence]: http://en.wikipedia.org/wiki/Subsequence
[listtoggle]: https://github.com/Valloric/ListToggle
[vim-build]: https://github.com/Valloric/YouCompleteMe/wiki/Building-Vim-from-source
[tracker]: https://github.com/Valloric/YouCompleteMe/issues?state=open
[issue18]: https://github.com/Valloric/YouCompleteMe/issues/18
[delimitMate]: https://github.com/Raimondi/delimitMate
[completer-api]: https://github.com/Valloric/YouCompleteMe/blob/master/python/completers/completer.py
[win-wiki]: https://github.com/Valloric/YouCompleteMe/wiki/Windows-Installation-Guide
