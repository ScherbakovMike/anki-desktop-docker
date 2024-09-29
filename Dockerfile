FROM ghcr.io/linuxserver/baseimage-kasmvnc:ubuntujammy

RUN \
        dpkg --configure -a && \
        apt-get update && \
        apt-get install -y libasound2 libegl1 libnss3 libxcb-xinerama0 python3-pyxdg tar wget zstd && \
        apt-get install -y anki && \
        dpkg --remove anki && \
        wget https://apps.ankiweb.net/downloads/archive/anki-23.12.1-linux-qt5.tar.zst && \
        zstd -d anki-23.12.1-linux-qt5.tar.zst --stdout | tar -xf - && \
        cd anki-23.12.1-linux-qt5 && ./install.sh &&  cd .. && \
        rm -rf anki-23.12.1-linux-qt5.tar.zst "anki-23.12.1-linux-qt5" && \
        apt-get clean

EXPOSE 3000 8765

VOLUME "/config/.local/share"

COPY /anki-data/ /config/.local/share/
COPY /root /

RUN chmod -R a+rw /config/.local/share/Anki /config/.local/share/Anki2
