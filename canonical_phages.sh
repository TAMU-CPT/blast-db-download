gdrive export -f --mime text/tab-separated-values 11fFcc71nC0lKkifvI75FCAHNG1O83hPUiQTFqV14Dcs
cat 'Canonical Phage Database.tsv' | awk -F'\t' '(NR>1){print $2"\t"$1}' > canonical_phages.list;
rm -f 'Canonical Phage Database.tsv'
