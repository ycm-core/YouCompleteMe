Writing good issue reports
==========================

First things first: **the issue tracker is NOT for tech support**. It is for
reporting bugs and requesting features. If your issue amounts to "I can't get
YCM to work on my machine" and the reason why is obviously related to your
machine configuration and the problem would not be resolved with _reasonable_
changes to the YCM codebase, then the issue is likely to be closed.

**A good place to ask questions is the [Gitter room][gitter] or the
[ycm-users][] Google group**. Rule of thumb: if you're not sure whether your
problem is a real bug, ask on the room or the group.

**YCM compiles just fine**; [the build bots say so][build-bots]. If the bots are
green and YCM doesn't compile on your machine, then _your machine is the root
cause_. Now read the first paragraph again.

Realize that quite literally _thousands_ of people have gotten YCM to work
successfully so if you can't, it's probably because you have a peculiar
system/Vim configuration or you didn't go through the docs carefully enough.
It's very unlikely to be caused by an actual bug in YCM because someone would
have already found it and reported it.

This leads us to point #2: **make sure you have checked the docs before
reporting an issue**. The docs are extensive and cover a ton of things; there's
also an FAQ at the bottom that quite possibly addresses your problem.

Further, **search the issue tracker for similar issues** before creating a new
one. There's no point in duplication; if an existing issue addresses your
problem, please comment there instead of creating a duplicate.

You should also **search the archives of the [ycm-users][] mailing list**.

Lastly, **make sure you are running the latest version of YCM**. The issue you
have encountered may have already been fixed. **Don't forget to recompile
ycm_core.so too** (usually by just running `install.py` again).

OK, so we've reached this far. You need to create an issue. First realize that
the time it takes to fix your issue is a multiple of how long it takes the
developer to reproduce it. The easier it is to reproduce, the quicker it'll be
fixed.

Here are the things you should do when creating an issue:

1. **Write a step-by-step procedure that when performed repeatedly reproduces
   your issue.** If we can't reproduce the issue, then we can't fix it. It's
   that simple.
2. Add the output of [the `:YcmDebugInfo` command][ycm-debug-info-command].
3. Put the following options in your vimrc:
   ```viml
   let g:ycm_keep_logfiles = 1
   let g:ycm_log_level = 'debug'
   ```

   Reproduce your issue and attach the contents of the logfiles. Use [the
   `:YcmToggleLogs` command][ycm-toggle-logs-command] to directly open them in
   Vim.
4. **Create a test case for your issue**. This is critical. Don't talk about how
   "when I have X in my file" or similar, _create a file with X in it_ and put
   the contents inside code blocks in your issue description. Try to make this
   test file _as small as possible_. Don't just paste a huge, 500 line source
   file you were editing and present that as a test. _Minimize_ the file so that
   the problem is reproduced with the smallest possible amount of test data.
5. **Include your OS and OS version.**
6. **Include the output of `vim --version`.**


Creating good pull requests
===========================

1.  **Follow the code style of the existing codebase.**
    - The Python code **DOES NOT** follow PEP 8. This is not an oversight, this
      is by choice. You can dislike this as much as you want, but you still need
      to follow the existing style. Look at other Python files to see what the
      style is.
    - The C++ code has an automated formatter (`style_format.sh` that runs
      `astyle`) but it's not perfect. Again, look at the other C++ files and
      match the code style you see.
    - Same thing for VimScript. Match the style of the existing code.

2.  **Your code needs to be well written and easy to maintain**. This is of the
    _utmost_ importance. Other people will have to maintain your code so don't
    just throw stuff against the wall until things kinda work.

3.  **Split your pull request into several smaller ones if possible.** This
    makes it easier to review your changes, which means they will be merged
    faster.

4.  **Write tests for your code**. If you're changing the VimScript code then
    you don't have to since it's hard to test that code. This is also why you
    should strive to implement your change in Python if at all possible (and if
    it makes sense to do so). Python is also _much_ faster than VimScript.

5.  **Explain in detail why your pull request makes sense.** Ask yourself, would
    this feature be helpful to others? Not just a few people, but a lot of YCM’s
    users? See, good features are useful to many. If your feature is only useful
    to you and _maybe_ a couple of others, then that’s not a good feature.
    There is such a thing as “feature overload”. When software accumulates so
    many features of which most are only useful to a handful, then that software
    has become “bloated”. We don’t want that.

    Requests for features that are obscure or are helpful to but a few, or are
    not part of YCM's "vision" will be rejected. Yes, even if you provide a
    patch that completely implements it.

    Please include details on exactly what you would like to see, and why. The
    why is important - it's not always clear why a feature is really useful. And
    sometimes what you want can be done in a different way if the reason for the
    change is known. _What goal is your change trying to accomplish?_


[build-bots]: https://travis-ci.org/Valloric/YouCompleteMe
[ycm-users]: https://groups.google.com/forum/?hl=en#!forum/ycm-users
[gitter]: https://gitter.im/Valloric/YouCompleteMe
[ycm-debug-info-command]: https://github.com/Valloric/YouCompleteMe#the-ycmdebuginfo-command
[ycm-toggle-logs-command]: https://github.com/Valloric/YouCompleteMe#the-ycmtogglelogs-command
