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

mitre_id = "N/A" if mitre_id_str.startswith("$") or not mitre_id_str.strip() else mitre_id_str

severity = 1
tags = ["wazuh", "automated"]
enrichment_type = ""
vt_score = ""
send_email = False

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
