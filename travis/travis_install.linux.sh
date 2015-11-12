# Linux installation

virtualenv -p python${YCMD_PYTHON_VERSION} ${YCMD_VENV_DIR}

if [[ ${VIMSCRIPT} ]]; then
  if [[ -d /tmp/vim/.git ]]; then
    pushd /tmp/vim
    git fetch
    if ! git diff --exit-code --quiet ..origin/master; then
      git reset --hard origin/master
      git clean -dfx
      need_build=1
    fi
    popd
  else
    git clone --depth 1 --single-branch https://github.com/vim/vim /tmp/vim
    need_build=1
  fi
  if [[ -n "${need_build}" ]]; then
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
