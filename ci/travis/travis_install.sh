#!/bin/bash

set -ev

# RVM overrides the cd, popd, and pushd shell commands, causing the
# "shell_session_update: command not found" error on macOS when executing those
# commands.
unset -f cd popd pushd

################
# Compiler setup
################

# We can't use sudo, so we have to approximate the behaviour of setting the
# default system compiler.

mkdir -p ${HOME}/bin

ln -s /usr/bin/g++-4.8 ${HOME}/bin/c++
ln -s /usr/bin/gcc-4.8 ${HOME}/bin/cc

export PATH=${HOME}/bin:${PATH}

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

export PATH="${PYENV_ROOT}/bin:${PATH}"

eval "$(pyenv init -)"

if [ "${YCM_PYTHON_VERSION}" == "2.7" ]; then
  # Tests are failing on Python 2.7.0 with the exception
  # "TypeError: argument can't be <type 'unicode'>"
  PYENV_VERSION="2.7.1"
else
  PYENV_VERSION="3.4.0"
fi

# In order to work with ycmd, python *must* be built as a shared library. This
# is set via the PYTHON_CONFIGURE_OPTS option.
export PYTHON_CONFIGURE_OPTS="--enable-shared"

pyenv install --skip-existing ${PYENV_VERSION}
pyenv rehash
pyenv global ${PYENV_VERSION}

# It is quite easy to get the above series of steps wrong. Verify that the
# version of python actually in the path and used is the version that was
# requested, and fail the build if we broke the travis setup
python_version=$(python -c 'import sys; print( "{0}.{1}".format( sys.version_info[0], sys.version_info[1] ) )')
echo "Checking python version (actual ${python_version} vs expected ${YCM_PYTHON_VERSION})"
test ${python_version} == ${YCM_PYTHON_VERSION}

pip install -r python/test_requirements.txt

# The build infrastructure prints a lot of spam after this script runs, so make
# sure to disable printing, and failing on non-zero exit code after this script
# finishes
set +ev
