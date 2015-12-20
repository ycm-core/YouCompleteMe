# Linux installation

virtualenv -p python${YCMD_PYTHON_VERSION} ${YCMD_VENV_DIR}

if [[ ${VIMSCRIPT} ]]; then
  if [[ ! -d /tmp/vim/.git ]]; then
    git clone --depth 1 --single-branch --branch v7.3.598 https://github.com/vim/vim /tmp/vim
    pushd /tmp/vim
    ./configure --prefix="/tmp/vim/build" --with-features=huge \
      --with-x --enable-pythoninterp --enable-fail-if-missing
    make -j2
    make install
    popd
  fi

  export PATH=/tmp/vim/build/bin:$PATH
  export DISPLAY=:99.0
  sh -e /etc/init.d/xvfb start
fi
