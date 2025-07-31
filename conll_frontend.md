# CoNLL-U trees as queries

[CoNLL-U](https://universaldependencies.org/format.html) is a data format commonly used to store Universal Dependencies (UD) treebanks.

CQP/Tree allows converting CoNLL-U trees into CQP queries. 
For instance, the CoNLL-U snippet

```conllu
1	analog	analog	ADJ	JJ	Degree=Pos	2	amod	_	TokenRange=0:6
2	camera	camera	NOUN	NN	Number=Sing	0	root	_	SpaceAfter=No|TokenRange=7:13
```

maps to 

```cqp
a:[(word = "camera") & (lemma = "camera") & (pos = "NOUN") & (msd = "NN") & (ufeats = "{'Number': 'Sing'}") & (deprel = "root")] []* b:[(word = "analog") & (lemma = "analog") & (pos = "ADJ") & (msd = "JJ") & (ufeats = "{'Degree': 'Pos'}") & (deprel = "amod") & dephead = a.ref] | b:[(word = "analog") & (lemma = "analog") & (pos = "ADJ") & (msd = "JJ") & (ufeats = "{'Degree': 'Pos'}") & (deprel = "amod")] []* a:[(word = "camera") & (lemma = "camera") & (pos = "NOUN") & (msd = "NN") & (ufeats = "{'Number': 'Sing'}") & (deprel = "root") & b.dephead = ref]
```

Note that:

- the order in which the tokens occur in the input CoNNL-U tree is ignored
- the various UD fields currently map to Korp attributes:
  - `FORM` maps to `word`
  - `UPOS` maps to `pos`
  - `XPOS` maps to `msd`
  - `feats` maps to `ufeats`
  - `lemma` and `deprel` do not change
  - `DEPS` and `MISC` are currently ignored

Trees can be left partially unspecified by leaving some fields blank (at the moment, all fields can be left blank excepts for `ID` and `HEAD`):

```conllu
1	a.*	_	ADJ	_	_	2	_	_	_
2	_	_	NOUN	_	_	0	_	_	_
```

In this case, the output is a much more general query:

```cqp
a:[(pos = "NOUN")] []* b:[(word = "a.*") & (pos = "ADJ") & dephead = a.ref] | b:[(word = "a.*") & (pos = "ADJ")] []* a:[(pos = "NOUN") & b.dephead = ref]
```

If `NOUN` is replaced with `NN` and `ADJ` with `JJ`, the result is [a valid Korp query](https://spraakbanken.gu.se/korp/#?corpus=attasidor,da,svt-2004,svt-2005,svt-2006,svt-2007,svt-2008,svt-2009,svt-2010,svt-2011,svt-2012,svt-2013,svt-2014,svt-2015,svt-2016,svt-2017,svt-2018,svt-2019,svt-2020,svt-2021,svt-2022,svt-2023,svt-nodate&search_tab=2&search=cqp%7Ca:%5B(pos%20%3D%20%22NN%22)%5D%20%5B%5D*%20b:%5B(word%20%3D%20%22a.*%22)%20%26%20(pos%20%3D%20%22JJ%22)%20%26%20a.dephead%20%3D%20ref%5D%20%7C%20b:%5B(word%20%3D%20%22a.*%22)%20%26%20(pos%20%3D%20%22JJ%22)%5D%20%5B%5D*%20a:%5B(pos%20%3D%20%22NN%22)%20%26%20dephead%20%3D%20b.ref%5D), analogous to [example.grew](resources/example.grew).
