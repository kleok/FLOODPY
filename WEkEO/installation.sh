
cd .. && pip install -e .
pip install folium && pip install markupsafe==2.0.1
cd aux && chmod +x install_snap.sh && ./install_snap.sh