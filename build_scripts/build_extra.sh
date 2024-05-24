# for reproducing the plots with matscibert

# clone MatSciBERT
git clone https://github.com/M3RG-IITD/MatSciBERT
mv MatSciBERT/ plots/MatSciBERT/

# assumes you've created extractor already with build.sh
conda activate extractor

conda install -y pytorch==1.7.0 cudatoolkit=10.1 -c pytorch
# assumes cloned to MatSciBERT/  
conda install --yes --file plots/MatSciBERT/requirements.txt