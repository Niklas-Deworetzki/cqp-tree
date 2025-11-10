# Step-by-step 

Do these steps to build a release of the package.

1. [ ] Check (and increment) the version number in [pyproject.toml](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/pyproject.toml)
2. [ ] Build the distribution package `python -m build`
3. [ ] Upload the distribution package `twine upload dist/*`
4. [ ] Update version number in [Dockerfile](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/docker/Dockerfile)
5. [ ] Commit and push
6. [ ] Create [Release on GitHub](https://github.com/Niklas-Deworetzki/cqp-tree/releases/new)
