## Setup

### Hardware

* Pin 6 : Ground common to strand (blue) and power supply
* Pin 12 : GPIO 18 for data, connected to strand (white)

Power supply injecting 12 VDC into strand (red) 


### Project
```
cd ~/Projects
git clone github.com:jlamoree/lava.git
cd lava
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


## Test

```
cd ~/Projects/lava
source venv/bin/activate
sudo venv/bin/python strandtest.py
```
