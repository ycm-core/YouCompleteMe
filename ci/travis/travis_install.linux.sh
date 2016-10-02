# Linux-specific installation

# We can't use sudo, so we have to approximate the behaviour of setting the
# default system compiler.

mkdir ${HOME}/bin

ln -s /usr/bin/g++-4.8 ${HOME}/bin/c++
ln -s /usr/bin/gcc-4.8 ${HOME}/bin/cc

export PATH=${HOME}/bin:${PATH}

# In order to work with ycmd, python *must* be built as a shared library. This
# is set via the PYTHON_CONFIGURE_OPTS option.
export PYTHON_CONFIGURE_OPTS="--enable-shared"
