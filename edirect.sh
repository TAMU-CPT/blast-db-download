if [ ! -e "edirect" ]; then
	perl -MNet::FTP -e \
	'$ftp = new Net::FTP("ftp.ncbi.nlm.nih.gov", Passive => 1);
	 $ftp->login; $ftp->binary;
	 $ftp->get("/entrez/entrezdirect/edirect.zip");'
	unzip -u -q edirect.zip
	rm edirect.zip
	./edirect/setup.sh
fi
export PATH=$PATH:$PWD/edirect
