# Exit immediately if a command returns a non-zero status.
set -e

test -d "$HOME/.pyenv/bin" && export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

pyenv global ${YCM_PYTHON_VERSION}

codecov --name "${CODECOV_JOB_NAME}"

set +e
