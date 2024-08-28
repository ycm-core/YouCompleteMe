FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL C.UTF-8

ARG VIM_VERSION=v9.1.0016
ARG YCM_VIM_PYTHON=python3
ARG NODE_MAJOR=18

RUN apt-get update && \
  apt-get -y dist-upgrade && \
  apt-get -y --no-install-recommends install \
                     gnupg \
                     locales \
                     tzdata \
                     language-pack-en \
                     sudo \
                     libncurses5-dev libncursesw5-dev \
                     git \
                     build-essential \
                     cmake \
                     python3-dev \
                     python3-pip \
                     python3-setuptools \
                     python3-wheel \
                     openjdk-11-jdk-headless \
                     nodejs \
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

# clean up
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* &&\
    rm -rf ~/.cache && \
    rm -rf $HOME/vim
