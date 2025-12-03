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
- Install ``python3``, ``gcc``, ``build-essential`` and ``python3-pip`` (You can skip it if you already installed)
- Create directory ``/opt/axtm``
- Copy and create all ``.py``, ``.ini`` and ``config.yml`` files to ``/opt/axtm``
- Create a new user ``axtm`` and change owner for ``config.yml`` to ``axtm``  
 ** In case of security, assign ``/usr/sbin/nologin`` to this user is recommended
- Install service by copy ``axtm.service`` and ``axtm-api.service`` to ``/etc/systemd/system``, and perform ``systemd daemon-reload``
- Use ``pip3 install -r requirements.txt`` to install dependencies
- Add tunnel config, enable and start the service

### API Access
The API Interface allows client dynamically update their endpoint address once their endpoint changed.  
- API is disabled by default, set ``enable`` to ``True`` in ``config.yml`` to enable API access
- API is listen to port ``5000`` by default, it is recommended to place API behind WAF or reverse proxy
- API requires ``GET`` request method, and requires client pass ``config``, ``key`` and ``src`` args
- Example Usage: ``http://<Server_URL>:5000/updatedst?config=<config_name>&key=<Your_API_Key>&src=<New_Endpoint_Address>``

### Domain Monitor
The domain monitor allows client to provide FQDN (e.g. domain.example.com) as their endpoint address.

### Note
- The config name can have any length, but it will only take first 6 letters as tunnel name. Please make sure first 6 
letters are not the same.

For example of ``config.yml``, please refer to [example-config.yml](https://github.com/xosadmin/axtm/blob/main/example-config.yml)  
