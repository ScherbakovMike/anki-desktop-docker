# Kubernetes deployment

Runs Anki desktop headless with the AnkiConnect API, logging in to AnkiWeb and
syncing automatically using credentials from a Secret.

## Apply

```bash
kubectl apply -f namespace.yaml

# Create the AnkiWeb credentials secret (do not commit real values):
kubectl -n anki create secret generic anki-ankiweb \
  --from-literal=ANKI_USERNAME='you@example.com' \
  --from-literal=ANKI_PASSWORD='your-password'
# (secret.example.yaml shows the equivalent manifest form.)

kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Access

```bash
# Web UI (KasmVNC)
kubectl -n anki port-forward svc/anki-desktop 3000:3000
# AnkiConnect API
kubectl -n anki port-forward svc/anki-desktop 8765:8765
curl localhost:8765 -d '{"action":"version","version":6}'
```

## How sync works

The image bundles the `anki-autosync` add-on. On startup it reads
`ANKI_USERNAME` / `ANKI_PASSWORD` from the environment (provided by the Secret
via `envFrom`), logs in to AnkiWeb, stores the resulting auth token in
`/config`, performs an initial sync (a full download on a fresh volume), and
then syncs every `ANKI_SYNC_INTERVAL` seconds.

- Credentials persist as a sync token on the PVC after first login, so the
  password is only needed for the initial authentication.
- `ANKI_FULL_SYNC_DIRECTION` (`download` default / `upload`) controls direction
  only for ambiguous full-sync conflicts.
- Alternative to the in-pod timer: disable it with `ANKI_SYNC_INTERVAL=0` and
  run a `CronJob` that POSTs `{"action":"sync","version":6}` to the AnkiConnect
  service.

Run a single replica only — Anki holds an exclusive lock on the collection.
