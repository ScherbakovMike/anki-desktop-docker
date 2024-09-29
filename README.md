# Anki Desktop (Docker Version)

This repository provides a containerized version of Anki, designed to support automation through add-ons like Anki-Connect.

The application is accessible via a web interface on port `3000`, while the API is available on port `8765`. 

Anki's configuration is stored in a volume mounted at `/config/.local/share` within the container.

## Component Versions
- **Anki**: 2.1.35

## Example of the `docker-compose.yml` file

    version: '3.8'

    services:
        anki-desktop:
            image: mikescherbakov/anki-desktop-docker:latest
            container_name: anki-desktop
            ports:
                - "3000:3000"
                - "8765:8765"
            volumes:
                - anki-data:/config/.local/share
            restart: unless-stopped
    volumes:
        anki-data:

## Feedback
Feel free to reach out at [scherbakov.mike@gmail.com](mailto:scherbakov.mike@gmail.com).

Feedback and pull requests are welcome!

## Links
[GitHub repository](https://github.com/ScherbakovMike/anki-desktop-docker)

[Docker Hub repository](https://hub.docker.com/repository/docker/mikescherbakov/anki-desktop-docker)
