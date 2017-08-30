#!/bin/sh
#
# Serve the Trac 1.2 sandbox. This assumes you have run ./tools/mkenv.sh
# beforehand.
#

if [ ! -d "venv-1.2" ] || [ ! -d "sandbox-1.2" ]; then
	echo "error: you need to run ./tools/mkenv.sh first"
	exit 1
fi


./venv-1.2/bin/tracd sandbox-1.2 -p 8082 --basic-auth=sandbox\-1.2,htpasswd,sandbox
