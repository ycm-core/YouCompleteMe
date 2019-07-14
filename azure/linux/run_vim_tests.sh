# Exit immediately if a command returns a non-zero status.
set -e

# Required to enable Homebrew on Linux.
eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
eval "$(pyenv init -)"

pyenv global ${YCM_PYTHON_VERSION}

./test/run_vim_tests

set +e

