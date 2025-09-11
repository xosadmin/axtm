# AXTM  
This is a python-based tunnel manager, which helps user easily create ip tunnel on Linux OS.  
  
### Brief information  
- Supported OS: Debian 11+ / Ubuntu 20.04+
- Supported Protocol: ``vxlan, gre, gretap, sit``
  
### Installation
There are two methods to install AXTM.

#### A. Use ``install.sh``
- Clone this project
- Using command ``bash install.sh``

#### B. Install manually
- Clone this project
- Install ``python3`` and ``python3-pip`` (You can skip it if you already installed)
- Create directory ``/opt/axtm``
- Copy and create ``conf.ini``, ``main.py`` to ``/opt/axtm``
- Install service by copy ``axtm.service`` to ``/etc/systemd/system``, and perform ``systemd daemon-reload``
- Use ``pip3 install -r requirements.txt`` to install dependencies
- Add tunnel config, enable and start the service

For example of ``conf.ini``, please refer to [conf.ini.example](https://github.com/xosadmin/axtm/blob/main/conf.ini.example)  
