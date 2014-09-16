#!/bin/sh
#
# Serve the Trac 0.12 sandbox. This assumes you have run ./tools/mkenv.sh
# beforehand.
#

if [ ! -d "venv-0.12" ] || [ ! -d "sandbox-0.12" ]; then
	echo "error: you need to run ./tools/mkenv.sh first"
	exit 1
fi

./venv-0.12/bin/tracd sandbox-0.12 -p 8080 --basic-auth=sandbox\-0.12,htpasswd,sandbox
