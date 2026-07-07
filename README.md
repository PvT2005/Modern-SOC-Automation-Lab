# Modern SOC Automation Lab

A personal project I built during my SOC L1 internship. Instead of just staring at pre-built dashboards, I wanted to actually understand how a SOC works under the hood — so I set up the whole thing from scratch in a virtual lab. It covers everything from collecting endpoint logs, writing custom detection rules, to building an automated incident response pipeline.

The stack combines **Wazuh** , **Shuffle** , **TheHive** and **VirusTotal** into one connected pipeline: detect → enrich → create case → notify analyst → block attacker automatically.

---

## Project Phases

### Phase 1 — Detection

Set up the monitoring and threat detection foundation. Installed Sysmon + Wazuh Agent on the endpoint, simulated 13 MITRE ATT&CK techniques using Atomic Red Team, wrote 36 custom detection rules from scratch, and verified that alerts fire correctly.

---

### Phase 2 — Automation

Turned the system from detect and forget into detect and respond automatically. Connected Wazuh → Shuffle → VirusTotal → TheHive → Email → Active Response into a full end-to-end SOAR pipeline.
