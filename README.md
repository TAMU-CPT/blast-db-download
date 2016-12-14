# Blast Downloader

We needed a simpler downloader, BioMAJ was a bit too complex for our needs.
Also I wanted JUnit output.

## Usage

First, customize download.py to taste, then:

```
python download.py > report.xml
```

There's an included script to automatically updated your `blastdb_p.loc` and `blastdb.loc` files

```
python gen_galaxy_loc.py $GALAXY_ROOT/tool-data/blastdb.loc $GALAXY_ROOT/tool-data/blastdb_p.loc
```

## License

BSD-3 Clause
