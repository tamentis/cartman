#!/bin/sh
#
# This script will create virtualenvs and trac environments for the purpose of
# hacking on cartman. The admin passwords on the sandboxes will be
# sandbox/sandbox.
#

rm -rf venv*
rm -rf sandbox*

# Set a common password for all the sandboxes.
htpasswd -b -c -m htpasswd sandbox sandbox

virtualenv venv-0.12
./venv-0.12/bin/pip install "trac<0.12.999"
./venv-0.12/bin/trac-admin sandbox-0.12 initenv "Sandbox for Trac 0.12" sqlite:db/trac.db
./venv-0.12/bin/trac-admin sandbox-0.12 permission add sandbox TRAC_ADMIN

virtualenv venv-1.0
./venv-1.0/bin/pip install "trac<1.0.999"
./venv-1.0/bin/trac-admin sandbox-1.0 initenv "Sandbox for Trac 1.0" sqlite:db/trac.db
./venv-1.0/bin/trac-admin sandbox-1.0 permission add sandbox TRAC_ADMIN

virtualenv venv-1.2
./venv-1.2/bin/pip install "trac<1.2.999"
./venv-1.2/bin/trac-admin sandbox-1.2 initenv "Sandbox for Trac 1.2" sqlite:db/trac.db
./venv-1.2/bin/trac-admin sandbox-1.2 permission add sandbox TRAC_ADMIN

htpasswd -b -c -m htpasswd sandbox sandbox
