#!/usr/bin/env bash

echo "cloning pdffigures2"
# clone pdffigures2
git clone https://github.com/allenai/pdffigures2

echo "installing sbt" 
# download sbt, from https://www.scala-sbt.org/download.html
echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list
echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | sudo tee /etc/apt/sources.list.d/sbt_old.list
curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo apt-key add
sudo apt-get update
sudo apt-get install sbt

python3.10 -m venv .venv
source .venv/bin/activate
pip install -r build_scripts/requirements.txt

# script run in sudo so need to give user access to cloned pdffigures dir
# (for python scripts later)
sudo chmod -R 777 pdffigures2
# build the thing - this was what caused the previous errors
cd pdffigures2
sudo sbt