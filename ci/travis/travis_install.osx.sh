# OS X-specific installation

# There's a homebrew bug which causes brew update to fail the first time. Run
# it twice to workaround. https://github.com/Homebrew/homebrew/issues/42553
brew update || brew update

# List of homebrew formulae to install in the order they appear.
# These are dependencies of pyenv.
REQUIREMENTS="ninja
              readline
              autoconf
              pkg-config
              openssl"

# Install pyenv and dependencies
for pkg in $REQUIREMENTS; do
  # Install package, or upgrade it if it is already installed
  brew install $pkg || brew outdated $pkg || brew upgrade $pkg
done

# In order to work with ycmd, python *must* be built as a shared library. The
# most compatible way to do this on OS X is with --enable-framework. This is
# set via the PYTHON_CONFIGURE_OPTS option
export PYTHON_CONFIGURE_OPTS="--enable-framework"
