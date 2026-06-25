# Base OS tag (rolling, one per OS). ubuntujammy = 22.04 (glibc 2.35);
# ubuntunoble = 24.04 (glibc 2.39). Override with --build-arg BASE_TAG=...
ARG BASE_TAG=ubuntujammy
FROM ghcr.io/linuxserver/baseimage-kasmvnc:${BASE_TAG}

# Anki release to install. As of 26.05 upstream ships a single Qt6 build per
# architecture (no more -qt5 variant) as a .tar.zst with an install.sh script.
ARG ANKI_VERSION=26.05
ARG ANKI_ARCH=x86_64

RUN \
        dpkg --configure -a && \
        # The jammy base ships a stale NodeSource node_18.x apt source that now
        # 404s and breaks apt-get update. We don't use Node, so drop it.
        rm -f /etc/apt/sources.list.d/nodesource*.list && \
        apt-get update && \
        apt-get install -y \
            libegl1 \
            libnss3 \
            libxcb-cursor0 \
            libxcb-icccm4 \
            libxcb-keysyms1 \
            libxcb-xinerama0 \
            python3-pyxdg \
            tar wget zstd && \
        # libasound2 was renamed libasound2t64 on Ubuntu 24.04 (time_t transition);
        # install whichever the base provides.
        ( apt-get install -y libasound2t64 || apt-get install -y libasound2 ) && \
        wget "https://github.com/ankitects/anki/releases/download/${ANKI_VERSION}/anki-${ANKI_VERSION}-linux-${ANKI_ARCH}.tar.zst" && \
        zstd -d "anki-${ANKI_VERSION}-linux-${ANKI_ARCH}.tar.zst" --stdout | tar -xf - && \
        cd anki-linux && ./install.sh && cd .. && \
        rm -rf "anki-${ANKI_VERSION}-linux-${ANKI_ARCH}.tar.zst" anki-linux && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*

EXPOSE 3000 8765

VOLUME "/config"

# Seed data (pre-installed AnkiConnect + anki-autosync add-ons and starter
# profile) is staged under /defaults and copied onto /config on first start by
# /etc/cont-init.d/50-anki-seed. This keeps the add-ons working even when /config
# is an empty Kubernetes PVC mounted over the image.
COPY /anki-data/ /defaults/anki-seed/
COPY /root /
