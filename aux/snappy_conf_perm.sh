# Install snappy permanently to Python (works on virtual enviroments also)
# Alekos Falagas (alek.falagas@gmail.com)

echo "Provide SNAP installation path:"
read -p "Is installation path /home/$USER/esa-snap/ and auxiliary path /home/$USER/.snap? [Y/n] " ANSWER
case "$ANSWER" in 
  [yY] | [yY][eE][sS])
    SNAP_INSTALLATION_FOLDER="/home/$USER/esa-snap"
    SNAP_AUX_FOLDER="/home/$USER/.snap"
    ;;
  [nN] | [nN][oO])
    read -p "Provide installation path: " SNAP_INSTALLATION_FOLDER
    read -p "Provide auxiliary path: " SNAP_AUX_FOLDER
    ;;
  *)
    echo "Error: Invalid option."
    exit 1
    ;;
esac

# Check if folders exist
if [ ! -d $SNAP_INSTALLATION_FOLDER ] 
then
  echo "Error: Directory $SNAP_INSTALLATION_FOLDER does not exists."
  exit 2
fi

if [ ! -d $SNAP_AUX_FOLDER ] 
then
  echo "Error: Directory $SNAP_AUX_FOLDER does not exists."
  exit 2
fi

SNAPPY_DIR=$SNAP_AUX_FOLDER"/snap-python/snappy/"

if [ ! -d $SNAPPY_DIR ] 
then
  echo "Error: Directory $SNAPPY_DIR does not exists. Try to configure snappy with $SNAP_INSTALLATION_FOLDER/bin/snappy_conf"
  exit 2
fi

read -p "Provide Python executable (e.g /usr/bin/python3):" PYTHON_PATH
if [ ! -f $PYTHON_PATH ]
then
  echo "Error: Provided python path does not exist."
  exit 2
fi

#Installing snappy
$PYTHON_PATH $SNAPPY_DIR"/setup.py" install 