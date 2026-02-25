# Deploy on SBX's demo server

After moving into this folder and checking out the `demo` branch:

1. `cd docker`
2. `podman compose build`
3. `podman compose up -d`

Debug mode:

```
podman compose run --rm --service-ports cqp-tree-web --log-level debug
```