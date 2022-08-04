# Get and install ESA-SNAP
# Alekos Falagas (alek.falagas@gmail.com)

# NO NEED FOR ROOT ACCESS is required for the instalation
URL="https://download.esa.int/step/snap/8.0/installers/esa-snap_all_unix_8_0.sh" 
SNAP=$(basename "$URL")
if [ ! -f $SNAP ] 
then
echo "Getting Linux installer from ESA..."
wget $URL
fi
# Change mode to executable
chmod +x $SNAP

# Start installation
echo "Installing SNAP..."
./$SNAP
echo "Done!"