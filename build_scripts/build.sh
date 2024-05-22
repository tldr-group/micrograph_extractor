#!/usr/bin/env bash

echo "cloning pdffigures2"
# clone pdffigures2
git clone https://github.com/allenai/pdffigures2

echo "installing sbt" 
# from oHo @ https://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linux
case "$(uname -sr)" in

   Darwin*)
     echo 'Mac OS X - needs brew to install'
     brew install sbt
     ;;

   Linux*Microsoft*)
     echo 'WSL'  # Windows Subsystem for Linux
     ;;

   Linux*)
   # download sbt, from https://www.scala-sbt.org/download.html
     echo 'Linux'
     echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list
     echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | sudo tee /etc/apt/sources.list.d/sbt_old.list
     curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo apt-key add
     # we need to install sbt as sudo - this causes problems later
     sudo apt-get update
     sudo apt-get install sbt
     ;;

   CYGWIN*|MINGW*|MINGW32*|MSYS*)
     echo 'MS Windows'
     exit 1
     ;;

   *)
     echo 'Other OS' 
     exit 1
     ;;
esac

python3.10 -m venv .venv
source .venv/bin/activate
pip install -r build_scripts/requirements.txt

# we need to make sure the user has access to the folder
sudo chmod o+rwx -R pdffigures2
# build the thing - this was what caused the previous errors
cd pdffigures2
# we need to run sbt as a normal user s.t python can call it later, so switch here
# need to pipe exit command into sbt
sudo -u $SUDO_USER sbt << EOF
exit
EOF
cd ..
sudo chmod o+rwx -R pdffigures2
# make sure venv has user permissions (so easy to delete)
sudo chmod o+rwx -R .venv
