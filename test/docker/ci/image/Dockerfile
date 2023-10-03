FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL C.UTF-8

ARG VIM_VERSION=v8.2.2735
ARG YCM_VIM_PYTHON=python3
ARG NODE_MAJOR=18

RUN mkdir -p /etc/apt/keyrings && \
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main"  \
    > /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && \
  apt-get -y dist-upgrade && \
  apt-get -y --no-install-recommends install ca-cacert \
                     locales \
                     tzdata \
                     language-pack-en \
                     libncurses5-dev libncursesw5-dev \
                     git \
                     build-essential \
                     cmake \
                     curl \
                     sudo \
                     python3-dev \
                     python3-pip \
                     python3-setuptools \
                     openjdk-11-jdk-headless \
                     npm \
                     vim-nox \
                     zlib1g-dev && \
  apt-get -y autoremove

RUN ln -fs /usr/share/zoneinfo/Europe/London /etc/localtime && \
  dpkg-reconfigure --frontend noninteractive tzdata

ENV CONF_ARGS "--with-features=huge \
               --enable-${YCM_VIM_PYTHON}interp \
               --enable-terminal \
               --enable-multibyte \
               --enable-fail-if-missing"

RUN mkdir -p $HOME/vim && \
    cd $HOME/vim && \
    git clone https://github.com/vim/vim && \
    cd vim && \
    git checkout ${VIM_VERSION} && \
    make -j 4 && \
    make install

# Python
RUN ${YCM_VIM_PYTHON} -m pip install --upgrade pip setuptools wheel

# clean up
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* &&\
    rm -rf ~/.cache && \
    rm -rf $HOME/vim
