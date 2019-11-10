# most of the following is taken from https://buildozer.readthedocs.io/en/latest/installation.html
sudo apt-get update
sudo apt-get install -y libgl1-mesa-dev git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake

pip install --upgrade cython virtualenv
pip install --upgrade buildozer

export PATH=$PATH:~/.local/bin/
      
# temporarily use my p4a fork with workaround, see comment in issue #3
git clone -b mapfix-workaround https://github.com/joergbrech/python-for-android.git /home/travis/build/joergbrech/python-for-android

