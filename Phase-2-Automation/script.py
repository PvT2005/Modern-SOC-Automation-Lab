import json

rule_level_str = "$exec.all_fields.rule.level"
vt_positives_str = "$vt_hash_lookup.#.body.data.attributes.last_analysis_stats.malicious"
ip_malicious_str = "$vt_ip_lookup.body.data.attributes.last_analysis_stats.malicious"
mitre_id_str = "$exec.all_fields.rule.mitre.id"

def safe_int(val, default_val=-1):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default_val

rule_level = safe_int(rule_level_str, 1)
vt_positives = safe_int(vt_positives_str)
ip_malicious = safe_int(ip_malicious_str)

# Xử lý MITRE ID sạch sẽ bằng Python thay vì Liquid
mitre_id = "N/A" if mitre_id_str.startswith("$") or not mitre_id_str.strip() else mitre_id_str

severity = 1
tags = ["wazuh", "automated"]
enrichment_type = ""
vt_score = ""
send_email = False

# ──────────────────────────────────────────────
# Nhánh A: File Hash Enrichment
# Áp dụng cho Sysmon EID 1 rules có sha256_hash:
#   100011(12), 100012(12), 100032(12), 100060(12),
#   100072(12), 100082(13), 100090(11), 100091(13),
#   100100(11), 100111(11), 100112(10), 100113(8),
#   100114(8), 100120(11), 100121(12), 100122(12)
# ──────────────────────────────────────────────
if vt_positives >= 0:
    enrichment_type = "file-hash"
    vt_score = str(vt_positives) + " engines detected"

    if vt_positives >= 10:
        severity = 3
        tags.append("confirmed-malicious")
        send_email = True
    elif vt_positives >= 1:
        severity = 2
        tags.append("suspicious")
        send_email = True
    else:
        if rule_level >= 12:
            severity = 2
        else:
            severity = 1
        tags.append("clean-on-vt")

# ──────────────────────────────────────────────
# Nhánh B: IP Reputation Enrichment
# Áp dụng cho rules có src_ip public:
#   100051(12) Brute Force 5+/60s
#   100053(15) Sustained Brute Force 100+/5m
#   100061(10) ADMIN$/C$ share access
# ──────────────────────────────────────────────
elif ip_malicious >= 0:
    enrichment_type = "ip-reputation"
    vt_score = str(ip_malicious) + " engines flagged this IP"

    if ip_malicious >= 5:
        severity = 3
        tags.append("malicious-ip")
        send_email = True
    elif ip_malicious >= 1:
        severity = 2
        tags.append("suspicious-ip")
        send_email = True
    else:
        if rule_level >= 12:
            severity = 2
        else:
            severity = 1
        tags.append("clean-ip")

# ──────────────────────────────────────────────
# Nhánh C: Behavioral (không hash, không IP public)
# Áp dụng cho các rules behavioral:
#   100001(10) LSASS access
#   100002(14) LSASS dump confirmed
#   100020(10) Registry Run Key
#   100021(13) Run Key by scripting engine
#   100030(8)  Scheduled Task created
#   100040(8)  Account created
#   100041(13) Added to Administrators
#   100070(8)  CreateRemoteThread
#   100071(14) Injection into system process
#   100073(13) DLL dropped in System32
#   100080(14) Security log cleared
#   100081(14) System log cleared
#   100101(13) Executable in Temp/AppData
# ──────────────────────────────────────────────
else:
    enrichment_type = "behavioral"
    vt_score = "N/A — Behavioral detection, no file/IP indicator for VT lookup"
    if rule_level >= 12:
        severity = 3
        send_email = True
    elif rule_level >= 10:
        severity = 2
    else:
        severity = 1

output = {
    "severity": severity,
    "tags": tags,
    "enrichment_type": enrichment_type,
    "vt_score": vt_score,
    "mitre_id": mitre_id,
    "send_email": send_email
}

print(json.dumps(output))
