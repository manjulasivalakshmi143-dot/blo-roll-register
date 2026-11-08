#!/bin/bash
# build both apps for all phones and copy them into the published repo
set -e
cd /home/claude/blo-register
python3 make_forms_app.py
mkdir -p dist/blo-forms
python3 build.py index.html dist/index.html
python3 build.py blo-forms/index.html dist/blo-forms/index.html
R=/home/claude/blo-roll-register
cp dist/index.html $R/index.html
cp dist/blo-forms/index.html $R/blo-forms/index.html
cp make_forms_app.py build.py publish.sh $R/blo-forms/ 2>/dev/null || true
v=$(grep -o 'blo-register-v[0-9]*' $R/sw.js | grep -o '[0-9]*$'); sed -i "s/blo-register-v$v/blo-register-v$((v+1))/" $R/sw.js
f=$(grep -o 'blo-forms-v[0-9]*' $R/blo-forms/sw.js | grep -o '[0-9]*$'); sed -i "s/blo-forms-v$f/blo-forms-v$((f+1))/" $R/blo-forms/sw.js
echo "ready: main v$((v+1)) forms v$((f+1))"
[ -d /home/claude/bloforms.github.io/.git ] && ./sync_bloforms.sh
