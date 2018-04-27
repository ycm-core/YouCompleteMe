#!/bin/bash

# Exit immediately if a command returns a non-zero status.
set -e

################
# Homebrew setup
################

# There's a homebrew bug which causes brew update to fail the first time. Run
# it twice to workaround. https://github.com/Homebrew/homebrew/issues/42553
brew update || brew update

# List of homebrew formulae to install in the order they appear.
# We require CMake for our build and tests, and all the others are dependencies
# of pyenv.
REQUIREMENTS="cmake
              readline
              autoconf
              pkg-config
              openssl"

# Install CMake and pyenv dependencies.
for pkg in $REQUIREMENTS; do
  # Install package, or upgrade it if it is already installed.
  brew install $pkg || brew outdated $pkg || brew upgrade $pkg
done

##############
# Python setup
##############

PYENV_ROOT="${HOME}/.pyenv"

if [ ! -d "${PYENV_ROOT}/.git" ]; then
  rm -rf ${PYENV_ROOT}
  git clone https://github.com/yyuu/pyenv.git ${PYENV_ROOT}
fi
pushd ${PYENV_ROOT}
git fetch --tags
git checkout v1.2.1
popd

PATH="${PYENV_ROOT}/bin:${PATH}"

eval "$(pyenv init -)"

if [ "${YCMD_PYTHON_VERSION}" == "2.7" ]; then
  # Prior versions fail to compile with error "ld: library not found for
  # -lSystemStubs"
  PYENV_VERSION="2.7.2"
else
  PYENV_VERSION="3.4.0"
fi

# In order to work with ycmd, python *must* be built as a shared library. The
# most compatible way to do this on macOS is with --enable-framework. This is
# set via the PYTHON_CONFIGURE_OPTS option.
export PYTHON_CONFIGURE_OPTS="--enable-framework"

pyenv install --skip-existing ${PYENV_VERSION}
pyenv rehash
pyenv global ${PYENV_VERSION}

# Initialize pyenv in other steps. See
# https://circleci.com/docs/2.0/env-vars/#interpolating-environment-variables-to-set-other-environment-variables
# and https://github.com/pyenv/pyenv/issues/264
echo "export PATH=${PYENV_ROOT}/bin:\$PATH
if [ -z \"\${PYENV_LOADING}\" ]; then
  export PYENV_LOADING=true
  eval \"\$(pyenv init -)\"
  unset PYENV_LOADING
fi" >> $BASH_ENV

pip install -r python/test_requirements.txt

set +e
