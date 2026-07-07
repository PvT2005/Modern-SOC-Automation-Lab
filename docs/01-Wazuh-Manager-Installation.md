# Installing Wazuh Manager on Ubuntu Server

This sets up the core of the SOC — the part that receives, analyzes and displays all the telemetry coming from endpoints.


## 1. Install Wazuh
 ```bash
curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh
sudo bash ./wazuh-install.sh -a
```
## 2. Access the Web Interface
- Open your browser and go to: https://192.168.56.10
- Log in with the admin account and the password generated during installation.
![wazuh-login](../screenshots/Wazuh-login.jpg)
- Dashboard view:
![wazuh-dashboard](../screenshots/Wazuh-Dashboard.jpg)
