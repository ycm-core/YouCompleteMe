# Exit immediately if a command returns a non-zero status.
set -e

sh -c "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install.sh)"

eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)

brew install openssl@1.0 pyenv

eval "$(pyenv init -)"

# In order to work with ycmd, python *must* be built as a shared library. This
# is set via the PYTHON_CONFIGURE_OPTS option.
PYTHON_CONFIGURE_OPTS="--enable-shared" \
CFLAGS="-I$(brew --prefix openssl@1.0)/include" \
LDFLAGS="-L$(brew --prefix openssl@1.0)/lib" \
pyenv install ${YCM_PYTHON_VERSION}
pyenv global ${YCM_PYTHON_VERSION}

pip install -r python/test_requirements.txt

set +e
