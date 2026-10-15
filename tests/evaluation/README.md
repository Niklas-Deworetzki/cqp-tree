# How to run Translation Evaluation

## Preparation

Run the following three commands from the **project root** to prepare Corpus Workbench and NoSketchEngine corpus files.

```bash
docker run --rm \
  --volume "$(pwd)/resources/evaluation:/corpora" \
  eltedh/nosketch-engine:latest \
  compilecorp --no-ske --recompile-corpus /corpora/registry/evalcorpus
docker run --rm \
  --volume "$(pwd)/resources/evaluation:/input" \
  --volume "$(pwd)/resources/cwb:/corpora" \
  ghcr.io/niklas-deworetzki/cwb:3.5 \
  cwb-encode -F /input/evalcorpus/vertical/ -d /corpora/data/evalcorpus -R /corpora/registry/evalcorpus \
  -c utf8 -p id -P word -P lemma -P upos -P xpos -P feats -P head -P deprel -P deps -P misc -S doc+id -S s+sent_id+text
docker run --rm \
  --volume "$(pwd)/resources/cwb:/corpora" \
  ghcr.io/niklas-deworetzki/cwb:3.5 \
  cwb-make -V EVALCORPUS
```
