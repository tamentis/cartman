#!/bin/sh
#
# Serve the Trac 1.0 sandbox. This assumes you have run ./tools/mkenv.sh
# beforehand.
#

if [ ! -d "venv-1.0" ] || [ ! -d "sandbox-1.0" ]; then
	echo "error: you need to run ./tools/mkenv.sh first"
	exit 1
fi


./venv-1.0/bin/tracd sandbox-1.0 -p 8081 --basic-auth=sandbox\-1.0,htpasswd,sandbox
