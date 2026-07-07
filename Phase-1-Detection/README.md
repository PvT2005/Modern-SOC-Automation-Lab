# Phase 1: Monitoring and Threat Detection

- Setting up the monitoring foundation — from collecting telemetry on the endpoint to analyzing, detecting and managing alerts based on the MITRE ATT&CK framework.

- This phase builds the SIEM with custom detection rules. All the events from the endpoint get collected and matched against these rules — if something looks suspicious, an alert gets created.



## Tools Used

- **Wazuh**: Handles log collection and analysis. It receives logs, matches them against detection rules and flags suspicious behavior.

- **Sysmon**: Deep monitoring on Windows. It tracks process creation, registry changes and network connections — way more detailed than default Windows Event Logs.

- **Atomic Red Team**: Open-source testing framework that maps directly to MITRE ATT&CK techniques. Used to simulate real attack techniques on the Windows endpoint to test if the detection rules actually work.



## How It Works

- **Telemetry Collection**: Sysmon and Windows Event Logs run on the endpoint and record what's happening. Wazuh Agent then sends these events to the Wazuh Manager.

- **Attack Simulation**: Atomic Red Team runs pre-built attack scripts mapped to specific MITRE ATT&CK Technique IDs. This is how I generate the events needed to build and test detection rules.

- **Analysis & Detection**: Wazuh Manager receives the logs and runs them through the custom rules. If something matches a suspicious pattern, it fires an alert.

- **Alerting**: Alerts show up on the Wazuh Dashboard with full details — Rule ID, severity level, affected endpoint info and MITRE ATT&CK mapping. This is the output of Phase 1, ready to be forwarded to Phase 2 via Webhook.


## Implementation Steps

1. Simulate attacks using Atomic Red Team on the target Windows machine.

| MITRE ID | Technique | Simulation Tool | Rule ID | 
|---|---|---|---|
| T1003.001 | OS Credential Dumping: LSASS Memory | Atomic Red Team | 100001–100002 | 
| T1059.001 | PowerShell Encoded / Bypass Execution | Atomic Red Team | 100010–100012 | 
| T1547.001 | Registry Run Keys / Startup Folder | Atomic Red Team | 100020–100021 |
| T1053.005 | Scheduled Task — Shell Payload | Atomic Red Team | 100030–100032 | 
| T1136.001 | Create Local Admin Account | Atomic Red Team | 100040–100041 | 
| T1110.001 | Brute Force Password Guessing | Script | 100050–100053 | 
| T1021.002 | Lateral Movement via SMB / PsExec | PsExec | 100060–100061 | 
| T1055.001 | Process Injection — DLL Injection | Atomic Red Team | 100070–100073 | 
| T1070.001 | Indicator Removal: Clear Event Logs | Atomic Red Team | 100080–100082 | 
| T1218.011 | LOLBas: Rundll32 Abuse | Atomic Red Team | 100090–100091 | 
| T1105 | Ingress Tool Transfer (certutil/bitsadmin) | Atomic Red Team | 100100–100101 | 
| T1082 | System Information Discovery / Recon | Atomic Red Team | 100110–100114 | 
| T1027 | Obfuscated Files / Payload Deobfuscation | Atomic Red Team | 100120–100122 |

2. Check the raw logs coming into the Wazuh Dashboard. 
3. Write detection rules in [local_rules.xml](./local_rules.xml) — 36 rules total (Rule ID `100001`–`100122`), each mapped to one of the 13 MITRE ATT&CK techniques. 
![rule](../screenshots/Wazuh_detection_rules.jpg)
4. Re-run the attack simulations to verify the rules. 
```
Invoke-AtomicTest T1082 -TestNumbers 1
Invoke-AtomicTest T1059.001 -TestNumbers 1 
Invoke-AtomicTest T1547.001 -TestNumbers 1
Invoke-AtomicTest T1053.005 -TestNumbers 1
Invoke-AtomicTest T1136.001 -TestNumbers 8
Invoke-AtomicTest T1003.001 -TestNumbers 1
Invoke-AtomicTest T1055.001 -TestNumbers 2 
Invoke-AtomicTest T1218.011 -TestNumbers 1
Invoke-AtomicTest T1105 -TestNumbers 7 
Invoke-AtomicTest T1027 -TestNumbers 2 
1..10 | ForEach-Object { net use \\127.0.0.1\IPC$ /user:fakeuser "WrongPass$_" 2>$null; Start-Sleep -Milliseconds 500 }
& "$env:TEMP\PsExec.exe" -accepteula \\127.0.0.1 cmd.exe /c "whoami"
Invoke-AtomicTest T1070.001 -TestNumbers 1
```
5. Confirm alerts fire correctly on the dashboard.
![1](../screenshots/Wazuh_security_alerts_1.jpg)
![2](../screenshots/Wazuh_security_alerts_2.jpg)
![3](../screenshots/Wazuh_security_alerts_3.jpg)
![4](../screenshots/Wazuh_security_alerts_4.jpg)
![5](../screenshots/Wazuh_security_alerts_5.jpg)
![6](../screenshots/Wazuh_security_alerts_6.jpg)

## Results

- SIEM up and running with Wazuh, collecting logs from Sysmon, Windows Security and Windows System on the target machine.
- Wrote 36 custom detection rules in `local_rules.xml` (ID `100001`–`100122`), covering 13 MITRE ATT&CK techniques — from credential dumping, persistence, brute force to lateral movement and defense evasion.

- Full log flow working: Endpoint → Sysmon → Wazuh Agent → Wazuh Manager → Dashboard, with alerts sorted by severity (Level 5–15).
