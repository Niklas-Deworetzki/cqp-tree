# fetched from https://raw.githubusercontent.com/LaboratorioSperimentale/adoc/refs/heads/main/src/tools.py
# TODO: curl


def parse_token(cols):
	header = ["id", "form", "lemma", "upos", "feats", "head", "deprel", "required", "without", "sem_feats", "sem_roles", "adjacency", "identity"]

	ret = {}
	for x, y in zip(header, cols):
		if x in ["id", "feats"]:
			ret[x]=y
		elif x in ["form", "lemma", "upos"]:
			ret[x] = y.split(",")
		elif x in ["required"]:
			ret[x]=bool(int(y))
		else:
			ret[x]=y

	return ret



# TODO: handle more than one construction
def parse(construction_str, mapping=None):

	construction = construction_str.split("\n")

	ret = { "metadata": [],
			"tokens": []
		}

	for line in construction:
		line = line.strip()
		if len(line):
			if line.startswith("#"):
				ret["metadata"].append(line[1:].split("="))
			else:
				new_token = parse_token(line.split("\t"))
				ret["tokens"].append(new_token)

	return ret


if __name__ == "__main__":
	with open("/Users/ludovica/Documents/projects/adoc/cxns_conllc/cxn_68.conllc") as fin:
		res = parse(fin.read())

		print(res["metadata"])
		for tok in res["tokens"]:
			print(tok)