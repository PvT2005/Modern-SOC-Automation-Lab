# Windows 10 Telemetry (Sysmon & Wazuh Agent)

The goal here is to turn a normal Windows machine into a sensor that continuously collects behavior data and sends it back to the SIEM on the Ubuntu Server.

## 1. Install Sysmon with SwiftOnSecurity Config
- Default Windows Event Logs are pretty limited. Sysmon gives you much better visibility — it captures things like process creation, network connections, and driver loads.
  - Config file used: [sysmonconfig.xml](../Phase-1-Detection/sysmonconfig.xml)


- Open PowerShell as Admin, navigate to the Sysmon folder and run:

```bash
.\Sysmon64.exe -i sysmonconfig.xml
```
After this, Sysmon will start logging events in Event Viewer.

## 2. Install Wazuh Agent and Connect to Server
Now that Sysmon is generating logs, we need Wazuh Agent to ship them to the Ubuntu Server.

- Configure Sysmon log forwarding:

  - Edit the file at C:\Program Files (x86)\ossec-agent\ossec.conf. Full config [here](../Phase-1-Detection/wazuh_manager_ossec.conf)

- Save the file and restart the Wazuh service to apply the changes.

## 3. Verify Everything Works
Last step — make sure the data pipeline is not broken.

- On Windows 10: Check that events are being generated continuously.
- On Wazuh Dashboard:
  - Go to Agents and confirm the Windows 10 machine shows as Active.
  - Go to Security Events and confirm logs from Windows are showing up.
