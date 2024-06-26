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

# from user cdub (https://stackoverflow.com/questions/70597896/check-if-conda-env-exists-and-create-if-not-in-bash)
find_in_conda_env(){
    conda env list | grep "${@}" >/dev/null 2>/dev/null
}

if find_in_conda_env "extractor" ; then
   echo "activating existing conda env"
   conda activate extractor
else 
   echo "creating conda env"
   conda env create -f build_scripts/environment.yaml
   conda activate extractor
fi
conda install --channel conda-forge --yes --file build_scripts/requirements.txt

# script run in sudo so need to give user access to cloned pdffigures dir
# (for python scripts later)
sudo chmod -R 777 pdffigures2
# build the thing
cd pdffigures2
sudo sbt