# Anki Desktop (Docker)

Run the [Anki](https://apps.ankiweb.net/) desktop app in a container, reachable
through a browser and automatable over HTTP via the
[Anki-Connect](https://foosoft.net/projects/anki-connect/) add-on. A bundled
add-on can log in to AnkiWeb and sync automatically from environment variables,
so it runs unattended on a server or in Kubernetes.

- **Web UI** (KasmVNC) on port **3000** — the full Anki GUI in your browser.
- **Anki-Connect API** on port **8765** — the standard automation API.
- **Headless AnkiWeb sync** — log in and sync without touching the GUI.
- **Persistent data** under `/config`.

Built on `ghcr.io/linuxserver/baseimage-kasmvnc`. Anki **26.05** (Qt6).

## Quick start

```bash
docker run -d --name anki-desktop \
  -p 3000:3000 -p 8765:8765 \
  -v anki-data:/config \
  -e PUID=1000 -e PGID=1000 \
  mikescherbakov/anki-desktop-docker:latest
```

Then open <http://localhost:3000> for the GUI, or call the API:

```bash
curl localhost:8765 -d '{"action":"version","version":6}'
# {"result": 6, "error": null}
```

To sync with AnkiWeb automatically, add your credentials:

```bash
docker run -d --name anki-desktop \
  -p 3000:3000 -p 8765:8765 \
  -v anki-data:/config \
  -e PUID=1000 -e PGID=1000 \
  -e ANKI_USERNAME='you@example.com' \
  -e ANKI_PASSWORD='your-password' \
  mikescherbakov/anki-desktop-docker:latest
```

### Docker Compose

A ready-to-use [`docker-compose.yml`](docker-compose.yml) is included. Put your
credentials in a `.env` file next to it:

```ini
ANKI_USERNAME=you@example.com
ANKI_PASSWORD=your-password
```

```bash
docker compose up -d
```

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `ANKI_USERNAME` | AnkiWeb account; enables automatic login | _(unset → no auto-login)_ |
| `ANKI_PASSWORD` | AnkiWeb password (only needed for the first login) | _(unset)_ |
| `ANKI_SYNC_INTERVAL` | Seconds between automatic syncs; `0` disables | `300` |
| `ANKI_FULL_SYNC_DIRECTION` | Direction for ambiguous full-sync conflicts: `download` or `upload` | `download` |
| `PUID` / `PGID` | User/group that owns the `/config` volume | `911` |
| `TZ` | Timezone | `Etc/UTC` |

## How AnkiWeb sync works

When `ANKI_USERNAME` and `ANKI_PASSWORD` are set, on startup the container:

1. logs in to AnkiWeb and stores the resulting **sync token** on the `/config`
   volume (the password is not stored, and is only needed for the first login);
2. performs an initial sync — a **full download** on a fresh volume, so your
   existing AnkiWeb collection is pulled in;
3. re-syncs every `ANKI_SYNC_INTERVAL` seconds.

If you leave the credentials unset, the container starts normally and you can
sign in through the web UI instead.

> **Full-sync direction:** when local and remote have diverged and Anki can't
> decide, `ANKI_FULL_SYNC_DIRECTION` picks the winner. The default `download`
> treats AnkiWeb as the source of truth (safe for a fresh container); use
> `upload` only if the container holds the canonical collection.

## Automating with Anki-Connect

The API on port `8765` accepts the standard
[Anki-Connect actions](https://foosoft.net/projects/anki-connect/#supported-actions).

```bash
# List decks
curl localhost:8765 -d '{"action":"deckNames","version":6}'

# Trigger a sync now
curl localhost:8765 -d '{"action":"sync","version":6}'

# Add a note
curl localhost:8765 -d '{
  "action":"addNote","version":6,
  "params":{"note":{
    "deckName":"Default","modelName":"Basic",
    "fields":{"Front":"hello","Back":"world"},"tags":["demo"]
  }}
}'
```

## Kubernetes

Manifests are in [`k8s/`](k8s/) — Namespace, PVC, Deployment, Service, and a
Secret example. AnkiWeb credentials come from a Kubernetes Secret. See
[`k8s/README.md`](k8s/README.md) for the apply steps.

## Data & persistence

Anki stores everything under `/config` (the collection lives in
`/config/.local/share`). Mount a volume there to keep your data across
restarts. The image ships with Anki-Connect and the auto-sync add-on
pre-installed; they are seeded onto the volume on first start.

Run a **single instance** per collection — Anki holds an exclusive lock on it.

## Building

```bash
docker build -t anki-desktop-docker .

# Pin a specific Anki release:
docker build --build-arg ANKI_VERSION=26.05 -t anki-desktop-docker .

# Build on a different base (default ubuntujammy / 22.04):
docker build --build-arg BASE_TAG=ubuntunoble -t anki-desktop-docker .
```

`ubuntujammy` uses noticeably less memory at idle and is the recommended base;
`ubuntunoble` (24.04) is available if you need glibc 2.39.

## Links

- [GitHub repository](https://github.com/ScherbakovMike/anki-desktop-docker)
- [Docker Hub repository](https://hub.docker.com/repository/docker/mikescherbakov/anki-desktop-docker)

## Feedback

Issues and pull requests are welcome. Contact:
[scherbakov.mike@gmail.com](mailto:scherbakov.mike@gmail.com).
