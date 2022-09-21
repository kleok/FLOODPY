# Get and install ESA-SNAP
# Alekos Falagas (alek.falagas@gmail.com)

INSTALLATION_DIR="$HOME/snap"
RESPONSE_FILE="./snap_auxdata/response.varfile"
GPT_OPTIONS="./snap_auxdata/gpt.vmoptions"
SYM_LINKS="/usr/local/bin"

# Setting installation path (line 12 of the response file)
sed -i '12s@.*@sys.installationDir='$INSTALLATION_DIR'@' $RESPONSE_FILE
# Setting symlinks path (line 15 of the response file)
sed -i '15s@.*@sys.symlinkDir='$SYM_LINKS'@' $RESPONSE_FILE

# Installing required libraries
REQUIRED_PKG="libgfortran5"
PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $REQUIRED_PKG|grep "install ok installed")
echo Checking for $REQUIRED_PKG: $PKG_OK
if [ "" = "$PKG_OK" ]; then
  echo "No $REQUIRED_PKG. Setting up $REQUIRED_PKG."
  sudo apt install $REQUIRED_PKG -y 
fi

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

# Automating installation with varfile
# Start installation
echo "Installing SNAP..."
./$SNAP -q -varfile $RESPONSE_FILE
echo "Done!"

cp $GPT_OPTIONS $INSTALLATION_DIR/bin/

rm $SNAP

# Update SNAP
cd $INSTALLATION_DIR/bin
./snap --nosplash --nogui --modules --update-all
