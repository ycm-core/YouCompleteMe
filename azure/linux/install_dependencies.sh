# Exit immediately if a command returns a non-zero status.
set -e

sudo apt-get update
sudo apt-get install libsqlite3-dev

sudo apt-get install -y build-essential \
                        libssl-dev \
                        zlib1g-dev \
                        libbz2-dev \
                        libreadline-dev \
                        libsqlite3-dev \
                        wget \
                        curl \
                        llvm \
                        libncurses5-dev \
                        libncursesw5-dev \
                        xz-utils \
                        tk-dev \
                        libffi-dev \
                        liblzma-dev \
                        python-openssl \
                        git
curl https://pyenv.run | bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

# In order to work with ycmd, python *must* be built as a shared library. This
# is set via the PYTHON_CONFIGURE_OPTS option.
PYTHON_CONFIGURE_OPTS="--enable-shared" \
CFLAGS="-I$(brew --prefix openssl)/include" \
LDFLAGS="-L$(brew --prefix openssl)/lib" \
  pyenv install ${YCM_PYTHON_VERSION}
pyenv global ${YCM_PYTHON_VERSION}
pip install -r python/test_requirements.txt

set +e

# vim: ft=bash
