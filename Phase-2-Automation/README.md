# Phase 2: SOC Automation & Automated Triage

Phase 2 takes the system from just detecting to actually responding. All the infrastructure (Wazuh Manager, TheHive) was already set up in Phase 1 — this phase focuses on connecting everything together and automating the workflow through Shuffle.

---

## Tools Used

- **Shuffle**: Open-source SOAR platform. It receives webhooks from Wazuh, handles the logic, calls external APIs and sends actions to TheHive + Email.

- **VirusTotal API**: File and IP reputation service. Shuffle automatically calls this API to enrich alerts as soon as they come in from Wazuh — no manual lookup needed.

- **TheHive**: Receives cases from Shuffle with enrichment data already filled in — the SOC team can jump straight into investigation.

- **Email**: Shuffle sends email notifications to the SOC analyst when an alert needs action. The analyst opens an approval form on Shuffle, picks Continue (block IP) or Stop. If they pick Continue → Wazuh Active Response automatically blocks the attacker's IP.


---

## Automation Flow


```
[1] Wazuh_alerts
     │
     ▼
[2] Extract_Hash
     │  Extract SHA256 
     │
     ├── [hash ≠ empty] ──► [3A] VT_Hash_Lookup ──► [4A] Format_VT_Score ──┐
     ├── [hash empty + IP] ► [3B] VT_IP_Lookup  ──► [4B] Format_IP_Score ──┤
     └── [hash empty,no IP]► [3C] Behavioral_Skip_VT ──────────────────────┘
                                                                             │
                                                                             ▼
                                                     [5] Dynamic_Severity_Scoring
                                                        
                                                                             │
                                                                             ▼
                                                         [6] Convert_Date
                                                          
                                                                             │
                                                                             ▼
                                                           [7] The_Hive
                                                          
                                                                             │
                                                                             ▼
                                                         [8] Get_Exec_ID
                                                          
                                                                             │
                                                                 [send_email = true]
                                                                             │
                                                                             ▼
                                                           [9] Email_App
                                                          
                                                                             │
                                                                             ▼
                                                       [10] Email_User_Input
                                                          
                                                                             │
                                                           [user approved + public IP exists]
                                                                             │
                                                                             ▼
                                                       [11] Get_Wazuh_Token
                                                          
                                                                             │
                                                                             ▼
                                                     [12] Wazuh_Active_Response
                                                        
                                                       → netsh block IP
```





## Implementation

### Install Shuffle SOAR

- Installed Shuffle self-hosted on the Ubuntu Server so it can reach the private IP `192.168.56.x` on the internal network.


- Access the Shuffle UI from the browser on the Windows machine:
`http://192.168.56.10:3001`

![Shuffle login page](../screenshots/Shuffle.jpg)

---

### Connect Wazuh → Shuffle

Add the `<integration>` block to `/var/ossec/etc/ossec.conf` on the Wazuh Manager. Only alerts with level 8 or higher get forwarded to keep the noise down:

```xml
<integration>
  <name>shuffle</name>
  <hook_url>http://192.168.56.10:3001/api/v1/hooks/<SHUFFLE_WEBHOOK_ID></hook_url>
  <level>8</level>
  <alert_format>json</alert_format>
</integration>
```



---

### Building the Workflow in Shuffle

The workflow has 15 nodes (13 actions + 2 triggers) that automatically classify alert data and pick the right VirusTotal API to call:

![Full Shuffle workflow](../screenshots/Workflow-shuffle.jpg)

---

**Node 1 — Wazuh_alerts**  
Entry point that receives data from Wazuh.

![Webhook node receiving JSON from Wazuh](../screenshots/Node_1.jpg)

---

**Node 2 — Extract Hash**  
Uses Shuffle Tools with the regex_capture_group action to pull the SHA256 hash from the Sysmon Hashes string.

Config:
- Input data: `$exec.all_fields.data.win.eventdata.hashes`
- Regex: `SHA256=([A-Fa-f0-9]{64})`


---

**Branching based on Extract_Hash**  

**Branch → VT_Hash_Lookup (Branch A — File Hash):**
```
Condition: $extract_hash IS NOT EMPTY
```


**Branch → VT_IP_Lookup (Branch B — IP Reputation):**
```
Condition: $extract_hash IS EMPTY
       AND $exec.all_fields.data.win.eventdata.ipAddress IS NOT EMPTY
       AND $exec.all_fields.data.win.eventdata.ipAddress DOES NOT MATCH "^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|::1|[fF][eE]80)"
```


**Branch → Behavioral_Skip_VT (Branch C — Behavioral):**
```
Condition: $extract_hash IS EMPTY
       AND ($exec.all_fields.data.win.eventdata.ipAddress MATCH ^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|::1|[fF][eE]80|$|.*ipAddress.*))
```

---

**Node 3A — VT_Hash_Lookup**  
Calls the VirusTotal API to check file reputation based on the SHA256 hash:
- App: `Virustotal_v3`
- Action: `Get a hash report`
- Hash: `$extract_hash`
- API Key
---

**Node 4A — Format_VT_Score**  
Uses `repeat_back_to_me` to format the VT result into a readable string:
```
$vt_hash_lookup.#.body.data.attributes.last_analysis_stats.malicious/
$vt_hash_lookup.#.body.data.attributes.last_analysis_stats.undetected engines detected
```
![](../screenshots/Node_4A.jpg)
---

**Node 3B — VT_IP_Lookup**  
Checks the source IP reputation on VirusTotal:
- App: `Virustotal_v3`
- Action: `Get an IP address report`
- IP: `$exec.all_fields.data.win.eventdata.ipAddress`

---

**Node 4B — Format_IP_Score**  
Formats the IP result into a string:
```
IP Reputation: $vt_ip_lookup.body.data.attributes.last_analysis_stats.malicious engines flagged
Country: $vt_ip_lookup.body.data.attributes.country
ASN: $vt_ip_lookup.body.data.attributes.as_owner
```
Example output: `"IP Reputation: 3 engines flagged | Country: CN | ASN: China Telecom"`


---

**Node 3C — Behavioral_Skip_VT**  
Sets a default string:
```
N/A — Behavioral detection, no file/IP indicator for VT lookup
```
![](../screenshots/Node_3C.jpg)
---

**Node 5 — Dynamic_Severity_Scoring**  
Merges results from all 3 branches (Format_VT_Score / Format_IP_Score / Behavioral_Skip_VT), calculates severity and decides whether to send an email. Uses [script.py](./script.py) for the scoring logic:

- When VT returns clean (0 engines detect), the script lowers severity since there's evidence the file/IP is clean. For behavioral alerts that don't call VT, there's nothing to lower the score — so severity stays based on rule_level.
- The Wazuh webhook already filters at `<level>8</level>`, so every alert hitting Shuffle has `rule_level >= 8`.
- Severity tiers based on Wazuh rule level: 12+ = HIGH, 10-11 = MEDIUM, 8-9 = LOW.


![](../screenshots/Node_5.jpg)

---

**Node 6 — Convert_Date**  
```python
import datetime
timestamp_str = "$exec.all_fields.timestamp"
dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
epoch_ms = int(dt.timestamp() * 1000)
print(epoch_ms)
```

---

**Node 7 — The_Hive (Create Alert/Case)**  
Connect TheHive to Shuffle:
- URL: `http://192.168.56.10:9000`
- API Key: Generated in TheHive

Alert fields config:
```text
Title:       [Wazuh-$exec.all_fields.rule.id] $exec.all_fields.rule.description
Severity:    $dynamic_severity_scoring.0.message.severity
Date:        $convert_date 
Source:      Wazuh-Shuffle-SOAR
Summary: 
  🖥️ Host: $exec.all_fields.agent.name
  📌 Rule: $exec.all_fields.rule.id
  🎯 MITRE: $dynamic_severity_scoring.0.message.mitre_id
  📊 Type: $dynamic_severity_scoring.0.message.enrichment_type
  🔍 VT Score: $dynamic_severity_scoring.0.message.vt_score
Tags:        ["wazuh", "automated", "phase2", "$dynamic_severity_scoring.0.message.enrichment_type"]
```
![](../screenshots/Thehive_Case.jpg)

---

**Node 8 — Get_Exec_ID**  
Gets the current Execution ID from the Shuffle API to build the approval form link for the analyst. This ID is used for the `frontend_continue` link in the email. The node calls the internal API:
```python
import requests, json
api_key = "<SHUFFLE_API_KEY>"
workflow_id = "<WORKFLOW_ID>"
url = f"http://192.168.56.10:5001/api/v1/workflows/{workflow_id}/executions"
headers = {"Authorization": f"Bearer {api_key}"}
resp = requests.get(url, headers=headers, timeout=10)
data = resp.json()
print(data[0].get("execution_id", "KEY_NOT_FOUND"))
```


---

**Email send decision**  
The condition `send_email = true` connects from `Get_Exec_ID` → `Email_App`:

```
Condition: $dynamic_severity_scoring.0.message.send_email equals true
    → TRUE:  Continue to Email_App and send notification
    → FALSE: Case is already saved in TheHive, no action needed
```

---

**Node 9 — Email_App**  
The built-in email feature of User Input is disabled on Shuffle self-hosted, so I used a separate `Email App` node to send notifications via SMTP.

SMTP config:
```
Action:    Send email smtp
Username:  <GMAIL_ADDRESS>
Password:  <GMAIL_APP_PASSWORD>    
SMTP host: smtp.gmail.com
SMTP port: 587
Recipient: <SOC_ANALYST_EMAIL>
```



![](../screenshots/Email.jpg)



---

**Node 10 — Email_User_Input**  
Creates an approval form and waits for the analyst to respond. The node goes into `WAITING` state — the workflow pauses until the analyst submits the form.
![](../screenshots/Node_10_1.jpg)

The analyst clicks Continue or Stop. The result gets passed to Node 11 with a branch condition checking if the user approved.
![](../screenshots/Node_10_2.jpg)

---

**Node 11 — Get_Wazuh_Token**  
Wazuh API requires JWT authentication. Need to call the authenticate endpoint first to get a token.

Config in Shuffle:
```
Method:     POST
URL:        https://192.168.56.10:55000/security/user/authenticate?raw=true
Headers:    Content-Type: application/json
Username:   wazuh
Password:   wazuh
Verify:     False        
Timeout:    10
```


![](../screenshots/Node_11.jpg)




**Node 12 — Wazuh_Active_Response**  
Only runs when all 3 conditions on the branch from Email_User_Input are met:
```
1. email.success equals true                          
2. $exec.all_fields.data.win.eventdata.ipAddress IS NOT EMPTY   
3. ipAddress DOES NOT MATCH ^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|::1|[fF][eE]80) 
```

Config in Shuffle:
```
Method:      PUT
URL:         https://192.168.56.10:55000/active-response
Headers:     Authorization: Bearer $get_wazuh_token.body
             Content-Type: application/json
Verify:      False
Timeout:     10
```

Body:
```json
{"command":"!netsh","alert":{"data":{"srcip":"$exec.all_fields.data.win.eventdata.ipAddress"}}}
```
![](../screenshots/Node_12.jpg)



---

### Wazuh Active Response Config on Ubuntu Server

To let Wazuh Manager receive and forward Active Response commands to the agent, add this to `/var/ossec/etc/ossec.conf` on the Ubuntu Server:

```xml
<command>
  <name>firewall-drop</name>
  <executable>firewall-drop</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <timeout>300</timeout>
</active-response>
```




Confirmed the IP block works (tested with dummy IP `1.2.3.4`):

![Windows Firewall blocking IP](../screenshots/Block_ip.jpg)

---



## Config Files

- [shuffle_workflow.json](./shuffle_workflow.json): The full Shuffle workflow export for the SOAR pipeline.



## Results

- Deployed Shuffle self-hosted, fully integrated with Wazuh and TheHive from Phase 1.
- Designed 3 processing branches: File Hash → VT File API, Source IP → VT IP API, Behavioral → skip VT. The workflow doesn't break when alerts are missing a hash or IP.
- Built Dynamic Severity Scoring — automatically adjusts case severity based on VirusTotal results, saves a lot of manual triage time.
- Set up Email App for alert notifications + Email User Input for the IP block approval form. Only triggers when the alert actually needs action (VT positive or rule level ≥ 12), reducing alert fatigue.
- Wazuh Active Response with JWT authentication — automatically blocks attacker IPs at the firewall level for 300 seconds.
- Every incident gets created as a case in TheHive automatically, with full enrichment data (VT score, IP reputation, or behavioral note) ready for deeper investigation.
