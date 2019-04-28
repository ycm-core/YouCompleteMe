# Exit immediately if a command returns a non-zero status.
set -e

brew install pyenv

eval "$(pyenv init -)"

# In order to work with ycmd, python *must* be built as a shared library. The
# most compatible way to do this on macOS is with --enable-framework. This is
# set via the PYTHON_CONFIGURE_OPTS option.
PYTHON_CONFIGURE_OPTS="--enable-framework" \
pyenv install ${YCM_PYTHON_VERSION}
pyenv global ${YCM_PYTHON_VERSION}

pip install -r python/test_requirements.txt

set +e
