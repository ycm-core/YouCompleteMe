#!/usr/bin/env bash
#
# Don't forget, this file needs to be idempotent, i.e. running it multiple times
# in a row leaves the system in the same state as if it were run only once.

#######################
# ENV VAR SETUP
#######################

# Makes apt-get STFU about pointless nonsense
export DEBIAN_FRONTEND=noninteractive

# For pyenv Python building
export CFLAGS='-O2'


#######################
# APT-GET INSTALL
#######################

apt-get update
apt-get -yqq dist-upgrade
apt-get install -yqq python-dev
apt-get install -yqq python-setuptools
apt-get install -yqq python3
apt-get install -yqq python3-dev
apt-get install -yqq python3-setuptools
apt-get install -yqq build-essential
apt-get install -yqq ninja-build
apt-get install -yqq cmake
apt-get install -yqq git
apt-get install -yqq golang
apt-get install -yqq mono-complete
apt-get install -yqq astyle

# These two are for pyopenssl
apt-get install -yqq libffi-dev
apt-get install -yqq libssl-dev

# These are Python build deps (though it depends on Python version). We need
# them because pyenv builds Python.
apt-get install -yqq libssl-dev
apt-get install -yqq zlib1g-dev
apt-get install -yqq libbz2-dev
apt-get install -yqq libreadline-dev
apt-get install -yqq libsqlite3-dev
apt-get install -yqq wget
apt-get install -yqq curl
apt-get install -yqq llvm
apt-get install -yqq libncurses5-dev
apt-get install -yqq libncursesw5-dev


#######################
# PIP SETUP
#######################

curl -sOL https://bootstrap.pypa.io/get-pip.py
python get-pip.py


#######################
# PYTHON LIBS
#######################

# We intentionally do NOT install the deps from test_requirements.txt into the
# system Python because that should help prevent accidental use of system Python
# during development. All dev work should happen with pyenv.

# This is needed to prevent InsecurePlatformWarning from showing up AFTER this
# stuff is installed.
pip install --upgrade pyopenssl ndg-httpsclient pyasn1


#######################
# NODEJS SETUP & LIBS
#######################

apt-get install -yqq nodejs

# Needed so that the node binary is named 'node' and not 'nodejs'; necessary
# because of scripts that call 'node'.
apt-get install -yqq nodejs-legacy
apt-get install -yqq npm

npm install -g typescript


#######################
# RUST SETUP
#######################

# multirust installation
echo "Installing multirust"
curl -sf https://raw.githubusercontent.com/brson/multirust/master/blastoff.sh \
  | sh -s -- --yes >/dev/null 2>&1

# Needs to run as vagrant user otherwise it only sets up a Rust toolchain for
# root, which doesn't do us any good.
su - vagrant -c "multirust default stable 2>/dev/null"


#######################
# PYENV SETUP
#######################

git clone https://github.com/yyuu/pyenv.git /home/vagrant/.pyenv

# Sourcing .profile to determine has provisioning already been done. If it has,
# then we don't re-add setup code.
source /home/vagrant/.profile
if [ -z "$PROVISIONING_DONE" ]; then
  echo 'export PROVISIONING_DONE=true' >> /home/vagrant/.profile
  echo 'export PYENV_ROOT="/home/vagrant/.pyenv"' >> /home/vagrant/.profile
  echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> /home/vagrant/.profile
  echo 'eval "$(pyenv init -)"' >> /home/vagrant/.profile
  echo 'cd /vagrant' >> /home/vagrant/.profile

  # In case we just created the file.
  chown vagrant:vagrant /home/vagrant/.profile

  # We need the newly-added commands from .profile in the current shell to run
  # pyenv.
  source /home/vagrant/.profile

  pyenv install 2.6.6
  pyenv install 3.3.6
  pyenv rehash

  # Avoid relying on the system python at all. Devs using some other
  # python is perfectly fine, but let's use a supported version by default.
  echo 'pyenv global 2.6.6' >> /home/vagrant/.profile
fi

# This installs libs in the pyenv Pythons in case the developer wants to run
# ycmd manually. NOTE: We use the latest lib versions here, not the versions
# that are used as submodules!
pyenv global 2.6.6
pip install -r /vagrant/python/test_requirements.txt
pip install -r /vagrant/examples/requirements.txt
pip install requests
pip install argparse
pip install bottle
pip install waitress
pip install ipdb
pip install ipdbplugin
pip install httpie
pip install coveralls

pyenv global 3.3.6
pip install -r /vagrant/python/test_requirements.txt
pip install -r /vagrant/examples/requirements.txt
pip install requests
pip install argparse
pip install bottle
pip install waitress
pip install ipdb
pip install ipdbplugin
pip install httpie
pip install coveralls

pyenv global system

chown -R vagrant:vagrant /home/vagrant/.pyenv
