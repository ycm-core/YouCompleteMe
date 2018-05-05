# Issue Prelude

**Please complete these steps and check these boxes (by putting an `x` inside
the brackets) _before_ filing your issue:**

- [ ] I have read and understood YCM's [CONTRIBUTING][cont] document.
- [ ] I have read and understood YCM's [CODE_OF_CONDUCT][code] document.
- [ ] I have read and understood YCM's [README][readme], **especially the
  [Frequently Asked Questions][faq] section.**
- [ ] I have searched YCM's issue tracker to find issues similar to the one I'm
  about to report and couldn't find an answer to my problem. ([Example Google
  search.][search])
- [ ] If filing a bug report, I have included the output of `vim --version`.
- [ ] If filing a bug report, I have included the output of `:YcmDebugInfo`.
- [ ] If filing a bug report, I have attached the contents of the logfiles using
  the `:YcmToggleLogs` command.
- [ ] If filing a bug report, I have included which OS (including specific OS
  version) I am using.
- [ ] If filing a bug report, I have included a minimal test case that reproduces
  my issue, including what I expected to happen and what actually happened.
- [ ] If filing a installation failure report, I have included the entire output
  of `install.py` (or `cmake`/`make`/`ninja`) including its invocation
- [ ] **I understand this is an open-source project staffed by volunteers and
  that any help I receive is a selfless, heartfelt _gift_ of their free time. I
  know I am not entitled to anything and will be polite and courteous.**
- [ ] **I understand my issue may be closed if it becomes obvious I didn't
  actually perform all of these steps.**

Thank you for adhering to this process! It ensures your issue is resolved
quickly and that neither your nor our time is needlessly wasted.

# Issue Details

> Provide a clear description of the problem, including the following key
> questions:

* What did you do?

> Include steps to reproduce here.

> Include description of a minimal test case, including any actual code required
> to reproduce the issue.

* What did you expect to happen?

> Include description of the expected behaviour.

* What actually happened?

> Include description of the observed behaviour, including actual output,
> screenshots, etc.

# Diagnostic data

## Output of `vim --version`

> Place the output here, or a link to a [gist][].

## Output of `YcmDebugInfo`

> Place the output here, or a link to a [gist][].

## Contents of YCM, ycmd and completion engine logfiles

> Add `let g:ycm_log_level = 'debug'` to vimrc, restart Vim, reproduce the
> issue, and include link here to a [gist][] containing the entire logfiles for
> ycm, ycmd and any completer logfiles listed by `:YcmToggleLogs`.

## OS version, distribution, etc.

> Include system information here.

## Output of build/install commands

> Include link to a [gist][] containing the invocation and entire output of
> `install.py` if reporting an installation issue.

[cont]: https://github.com/Valloric/YouCompleteMe/blob/master/CONTRIBUTING.md
[code]: https://github.com/Valloric/YouCompleteMe/blob/master/CODE_OF_CONDUCT.md
[readme]: https://github.com/Valloric/YouCompleteMe/blob/master/README.md
[faq]: https://github.com/Valloric/YouCompleteMe/blob/master/README.md#faq
[search]: https://www.google.com/search?q=site%3Ahttps%3A%2F%2Fgithub.com%2FValloric%2FYouCompleteMe%2Fissues%20python%20mac
[gist]: https://gist.github.com/
