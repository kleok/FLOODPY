# Get and install ESA-SNAP
# Alekos Falagas (alek.falagas@gmail.com)
read -p "UID: " CDSUID
read -p "API key: " CDSPASSWORD

URL="url: https://cds.climate.copernicus.eu/api/v2"

#Path to file
CDSFILEPATH="/home/$USER/.cdsapirc"
if [ ! -f $CDSFILEPATH ] 
then
    touch $CDSFILEPATH
    echo $URL >> $CDSFILEPATH
    echo "key:" $CDSUID:$CDSPASSWORD >> $CDSFILEPATH
else
    truncate -s 0 $CDSFILEPATH
    echo $URL >> $CDSFILEPATH
    echo "key:" $CDSUID:$CDSPASSWORD >> $CDSFILEPATH
fi
    
