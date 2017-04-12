db.json:
	python extract-phagedb.py < out2.gb > db.json

out2.gb:
	./edirect/esearch -db nucleotide -query 'txid28883[Organism:exp] AND ("20000"[SLEN] : "1000000"[SLEN])' | ./edirect/efetch -format gbwithparts > out2.gb
