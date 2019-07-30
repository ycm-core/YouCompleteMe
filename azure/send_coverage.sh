# Exit immediately if a command returns a non-zero status.
set -e

# Required to enable Homebrew on Linux.
test -d /home/linuxbrew/.linuxbrew && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
eval "$(pyenv init -)"

pyenv global ${YCM_PYTHON_VERSION}

if [ -n "$1" ]; then
  pushd $1
fi

if [ -f "coverage.xml" ]; then
  codecov --name "${CODECOV_JOB_NAME}" --file=coverage.xml
else
  codecov --name "${CODECOV_JOB_NAME}"
fi

if [ -n "$1" ]; then
  popd
fi

set +e
