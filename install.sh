sudo apt install -y python3-picamera2 libpcap-dev i2c-tools

python3 -m venv env
echo "alias env='source env/bin/activate'" >> ~/.bashrc
source env/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
