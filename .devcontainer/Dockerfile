FROM ubuntu
EXPOSE 5000

######### Apt dependencies

ARG system_apt_dependencies="build-essential cmake gdb automake autoconf libtool git pkg-config python3 python3-pip sudo"
ARG choco_apt_dependencies="gcc make libsdl2-dev libsdl2-net-dev libsdl2-mixer-dev"
ARG choco_apt_dependencies_optional="libflac-dev libfluidsynth-dev libpng-dev libsamplerate-dev libvorbis-dev"
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -qq $system_apt_dependencies $choco_apt_dependencies $choco_apt_dependencies_optional

########## Install via pip, not apt

ARG choco_pip_dependencies="pillow flask"
RUN pip install --break-system-packages $choco_pip_dependencies

########## Container user setup

# Remove any existing user with UID 1000
RUN USERNAME=$(getent passwd 1000 | cut -d: -f1) && \
    if [ -n "$USERNAME" ]; then userdel -r $USERNAME; fi

# Args
ARG USERNAME=chocodev
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# Add sudo support
RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Add the user to the audio group, to have ALSA sound access
# TODO: pulseaudio, so this isn't necessary?
RUN usermod -aG audio $USERNAME

# Use bash, not sh. Yuck.
RUN chsh $USERNAME -s /bin/bash

USER $USERNAME

# Make sure we actually own our own local share stuff
RUN mkdir -p /home/$USERNAME/.local/share && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME/.local
