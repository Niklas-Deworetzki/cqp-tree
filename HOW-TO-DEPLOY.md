To deploy on SBX's demo server:

1. `cd docker`
2. `podman compose build`
3. `podman compose up -d`

Debug mode:

```
podman compose run --rm --service-ports cqp-tree-web --log-level debug
```