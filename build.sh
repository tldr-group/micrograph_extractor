
VENV=1
PYTHON=1
CLONE=0
SBT=0
# python setup
if [ "$VENV" -eq 1 ]; then
  echo "Creating venv"
  python3.10 -m venv .venv
  .venv/bin/activate
fi

if [ "$PYTHON" -eq 1 ]; then
    pip install -r requirements.txt
fi

# clone pdffigures2
if [ "$CLONE" -eq 1 ]; then
    git clone https://github.com/allenai/pdffigures2
fi

# download sbt, from https://www.scala-sbt.org/download.html
if [ "$SBT" -eq 1 ]; then
    echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list
    echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | sudo tee /etc/apt/sources.list.d/sbt_old.list
    curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo apt-key add
    sudo apt-get update
    sudo apt-get install sbt
fi
# test extractor