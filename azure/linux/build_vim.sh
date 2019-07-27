# Exit immediately if a command returns a non-zero status.
set -e

eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)

pyenv global ${YCM_PYTHON_VERSION}

if [ -d ~/vim ]; then
  rm -rf ~/vim
fi

git clone --depth=1 --no-tags --branch ${YCM_VIM_VERSION}\
          https://github.com/vim/vim
pushd vim
  ./configure --with-features=huge \
              --enable-terminal \
              --enable-multibyte \
              --enable-fail-if-missing \
              ${YCM_VIM_PYTHON}
  make -j 4
  sudo make install
popd

# Also build ycmd
python install.py --clangd-completer

set +e
