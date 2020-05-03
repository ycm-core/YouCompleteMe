ARG YCM_PYTHON=py3

FROM youcompleteme/ycm-vim-${YCM_PYTHON}:test

RUN apt-get update && \
  apt-get -y --no-install-recommends install less && \
  apt-get -y autoremove

RUN useradd -ms /bin/bash -d /home/dev -G sudo dev && \
    echo "dev:dev" | chpasswd && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/sudo

USER dev
WORKDIR /home/dev

ENV HOME /home/dev
ENV PYTHON_CONFIGURE_OPTS --enable-shared

ADD --chown=dev:dev .vim/ /home/dev/.vim/

## cleanup of files from setup
RUN sudo rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

