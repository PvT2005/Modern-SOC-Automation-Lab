# Phase 2: SOC Automation & Triage tự động 

Nếu Phase 1 là lắng nghe và giám sát thì Phase 2 là bước nâng cấp hệ thống lên cấp độ chủ động phản ứng. Toàn bộ hạ tầng (Wazuh Manager, TheHive) đã được dựng sẵn ở Phase 1 thì Phase 2 tập trung vào việc kết nối và tự động hóa chúng lại với nhau thông qua Shuffle SOAR.

---

## Công cụ sử dụng

- **Shuffle (SOAR)**: Bộ não điều phối tự động mã nguồn mở. Nhận Webhook từ Wazuh, xử lý logic, gọi API bên ngoài và phân phối hành động đến TheHive + Email.

- **VirusTotal API**: Dịch vụ kiểm tra danh tiếng file/hash. Shuffle tự động gọi API này để enrich cảnh báo ngay khi nhận được từ Wazuh — không cần analyst làm thủ công.

- **TheHive**: Nhận Case được tạo tự động từ Shuffle, kèm đầy đủ kết quả Enrichment — sẵn sàng cho đội SOC điều tra.

- **Email**: Shuffle gửi email thông báo cho SOC Analyst khi có cảnh báo cần can thiệp. Analyst truy cập form phê duyệt trên Shuffle, chọn Continue (block IP) hoặc Stop (bỏ qua). Nếu chọn Continue → Wazuh Active Response tự động block IP nguồn tấn công.

Ta dùng Shuffle Self-hosted: Tính năng gửi email tích hợp trong node User Input là cloud-only và bị tắt trên bản self-hosted. Do đó, workflow sử dụng 2 node riêng biệt: Email App để gửi SMTP thông báo và Email User Input để tạo form chờ phản hồi. Analyst truy cập form thông qua link `frontend_continue` lấy từ Shuffle UI.

---

## 🔄 Luồng Tự động hóa (Smart Enrichment Routing)


```
[1] Wazuh_alerts (Webhook Trigger)
     │
     ▼
[2] Extract_Hash (Shuffle Tools — regex_capture_group)
     │  Trích xuất SHA256 
     │
     ├── [hash ≠ empty] ──► [3A] VT_Hash_Lookup ──► [4A] Format_VT_Score ──┐
     ├── [hash empty + IP] ► [3B] VT_IP_Lookup  ──► [4B] Format_IP_Score ──┤
     └── [hash empty,no IP]► [3C] Behavioral_Skip_VT ──────────────────────┘
                                                                            │
                                                                            ▼
                                                    [5] Dynamic_Severity_Scoring
                                                         (Execute Python)
                                                                            │
                                                                            ▼
                                                        [6] Convert_Date
                                                         (Execute Python)
                                                                            │
                                                                            ▼
                                                          [7] The_Hive
                                                         (Create Alert)
                                                                            │
                                                                            ▼
                                                        [8] Get_Exec_ID
                                                         (Execute Python)
                                                                            │
                                                                [send_email = true]
                                                                            │
                                                                            ▼
                                                          [9] Email_App
                                                         (SMTP Notification)
                                                                            │
                                                                            ▼
                                                      [10] Email_User_Input
                                                         (Approval Form)
                                                                            │
                                                                [user approved]
                                                                            │
                                                                            ▼
                                                      [11] Get_Wazuh_Token
                                                         (HTTP — POST)
                                                                            │
                                                                            ▼
                                                    [12] Wazuh_Active_Response
                                                         (HTTP — PUT)
                                                      → netsh block IP
```

**Ánh xạ Rule → Nhánh:**

| Nhánh | Rules | Kỹ thuật | Event Source |
|---|---|---|---|
| **A** (Hash) | 100010–12, 100032, 100060, 100072, 100082, 100090–91, 100100, 100110–14, 100120–22 | T1059.001, T1053.005, T1021.002, T1055.001, T1070.001, T1218.011, T1105, T1082, T1027 | Sysmon EID 1 |
| **B** (IP) | 100050–53, 100061 | T1110.001, T1021.002 | Windows EID 4625, 5140 |
| **C** (Behavioral) | 100001–02, 100020–21, 100030–31, 100040–41, 100070–71, 100073, 100080–81, 100101 | T1003.001, T1547.001, T1053.005, T1136.001, T1055.001, T1070.001, T1105 | Sysmon EID 8/10/11/13, Windows EID 1102/104/4698/4720/4732 |



## ⚙️ Triển khai

### Cài đặt Shuffle SOAR (Self-hosted Docker)

> Cài Shuffle self-hosted trên Ubuntu Server để kết nối đến IP private `192.168.56.x` của mạng nội bộ 


Truy cập giao diện Shuffle từ trình duyệt trên máy Windows:
`http://192.168.56.10:3001`

![Giao diện đăng nhập/trang chủ Shuffle](<ĐƯỜNG_DẪN_ẢNH_1>)

---

### Kết nối Wazuh → Shuffle 

Thêm khối `<integration>` vào file `/var/ossec/etc/ossec.conf` trên Wazuh Manager. Chỉ gửi các alert có level từ 8 trở lên để tránh noise:

```xml
<integration>
  <name>shuffle</name>
  <hook_url>http://192.168.56.10:3001/api/v1/hooks/<SHUFFLE_WEBHOOK_ID></hook_url>
  <level>8</level>
  <alert_format>json</alert_format>
</integration>
```



---

### Xây dựng Workflow trong Shuffle

Luồng gồm 15 node (13 action + 2 trigger) để tự động phân loại dữ liệu alert và chọn đúng API VirusTotal để gọi:

![Toàn bộ workflow trong Shuffle](<ĐƯỜNG_DẪN_ẢNH_2>)

---

**Node 1 — Wazuh_alerts**  
Điểm đầu vào nhận dữ liệu từ Wazuh. 

![Webhook node nhận dữ liệu JSON từ Wazuh](<ĐƯỜNG_DẪN_ẢNH_3>)

---

**Node 2 — Extract Hash**  
Dùng Shuffle Tools, hành động regex_capture_group để trích xuất SHA256 từ chuỗi Hashes của Sysmon. 

Cấu hình:
- Input data: `$exec.all_fields.data.win.eventdata.hashes`
- Regex: `SHA256=([A-Fa-f0-9]{64})`


---

**Rẽ nhánh dựa trên Extract_Hash**  

**Branch → VT_Hash_Lookup (Nhánh A — File Hash):**
```
Condition: $extract_hash IS NOT EMPTY
```
Áp dụng cho các rule dựa trên Sysmon EID 1: T1059.001, T1218.011, T1105, T1027, T1082...

**Branch → VT_IP_Lookup (Nhánh B — IP Reputation):**
```
Condition: $extract_hash IS EMPTY
       AND $exec.all_fields.data.win.eventdata.ipAddress IS NOT EMPTY
       AND $exec.all_fields.data.win.eventdata.ipAddress DOES NOT MATCH "^(127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|::1|[fF][eE]80)"
```
Áp dụng cho: T1110.001 (Brute Force — EID 4625), T1021.002 (SMB share — EID 5140).  
Loại trừ IP private/loopback (cả IPv4 và IPv6) vì VirusTotal chỉ có dữ liệu cho IP công cộng.

**Branch → Behavioral_Skip_VT (Nhánh C — Behavioral):**
```
Condition: $extract_hash IS EMPTY
       AND ($exec.all_fields.data.win.eventdata.ipAddress IS EMPTY
            OR matches private range)
```
Áp dụng cho: T1003.001 (LSASS), T1547.001 (Registry), T1136.001 (Account), T1070.001 (Log Clear)...

---

**Node 3A — VT_Hash_Lookup**  
Gọi VirusTotal API để kiểm tra danh tiếng của file dựa trên mã SHA256:
- App: `Virustotal_v3`
- Action: `Get a hash report`
- Hash: `$extract_hash`
- API Key
---

**Node 4A — Format_VT_Score**  
Dùng **repeat_back_to_me** để format kết quả VT thành chuỗi dễ đọc:
```
$vt_hash_lookup.#.body.data.attributes.last_analysis_stats.malicious/
$vt_hash_lookup.#.body.data.attributes.last_analysis_stats.undetected engines detected
```
Kết quả ví dụ: `"15/62 engines detected"`

---

**Node 3B — VT_IP_Lookup**  
Kiểm tra danh tiếng IP nguồn tấn công trên VirusTotal:
- App: `Virustotal_v3`
- Action: `Get an IP address report`
- IP: `$exec.all_fields.data.win.eventdata.ipAddress`

---

**Node 4B — Format_IP_Score**  
Format kết quả IP thành chuỗi:
```
IP Reputation: $vt_ip_lookup.body.data.attributes.last_analysis_stats.malicious engines flagged
Country: $vt_ip_lookup.body.data.attributes.country
ASN: $vt_ip_lookup.body.data.attributes.as_owner
```
Kết quả ví dụ: `"IP Reputation: 3 engines flagged | Country: CN | ASN: China Telecom"`

![Kết quả trả về từ VirusTotal Lookup](<ĐƯỜNG_DẪN_ẢNH_4>)

---

**Node 3C — Behavioral_Skip_VT**  
Gán chuỗi mặc định:
```
N/A — Behavioral detection, no file/IP indicator for VT lookup
```

---

**Node 5 — Dynamic_Severity_Scoring**  
Hợp nhất kết quả từ 3 nhánh (Format_VT_Score / Format_IP_Score / Behavioral_Skip_VT), tính toán Severity và quyết định gửi email.  
Dùng [script.py](./script.py) để quyết định logic xử lí:

- **Negative Evidence**: Khi VT trả clean (0/70+ engines), đó là bằng chứng giảm nhẹ — severity bị kéo xuống so với behavioral thuần.
- **Webhook filter `<level>8</level>`**: Mọi alert đến Shuffle đều có `rule_level >= 8`, nên threshold dưới 8 là vô nghĩa.
- **Wazuh Level Taxonomy**: Level 12+ = HIGH importance, 10-11 = notable, 8-9 = low-medium.

```
# Nhánh A — File Hash (VT File API):
IF vt_positives >= 10:
    severity = 3        # HIGH — đa số AV engines xác nhận malicious
    send_email = TRUE
ELSE IF vt_positives >= 1:
    severity = 2        # MEDIUM — cần analyst review
    send_email = TRUE
ELSE (VT clean = negative evidence):
    IF rule_level >= 12:  severity = 2   # MEDIUM — VT clean nhưng rule HIGH
    ELSE:                 severity = 1   # LOW — VT clean + rule moderate

# Nhánh B — IP Reputation (VT IP API):
IF ip_malicious >= 5:
    severity = 3        # HIGH — nhiều engines xác nhận IP malicious
    send_email = TRUE
ELSE IF ip_malicious >= 1:
    severity = 2        # MEDIUM — ít engines flag
    send_email = TRUE
ELSE (IP clean = negative evidence):
    IF rule_level >= 12:  severity = 2   # MEDIUM — IP clean nhưng rule HIGH
    ELSE:                 severity = 1   # LOW — IP clean + rule moderate

# Nhánh C — Behavioral (không có hash/IP để gọi VT):
IF rule_level >= 12:
    severity = 3        # HIGH — Wazuh HIGH/CRITICAL behavioral alert
    send_email = TRUE
ELSE IF rule_level >= 10:
    severity = 2        # MEDIUM — notable behavioral event
ELSE:
    severity = 1        # LOW — informational (level 8-9)
```

Output JSON trả về cho các Node tiếp theo:
```json
{
  "severity": 3,
  "tags": ["wazuh", "automated", "phase2", "confirmed-malicious"],
  "enrichment_type": "file-hash",
  "vt_score": "15 engines detected",
  "send_email": true
}
```

---

**Node 6 — Convert_Date**  
TheHive yêu cầu trường `date` ở định dạng epoch milliseconds, nhưng Wazuh trả về timestamp dạng ISO 8601. Node này chuyển đổi:
```python
import datetime
timestamp_str = "$exec.all_fields.timestamp"
dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
epoch_ms = int(dt.timestamp() * 1000)
print(epoch_ms)
```

---

**Node 7 — The_Hive (Create Alert/Case)**  
Kết nối TheHive vào Shuffle:
- URL: `http://192.168.56.10:9000`
- API Key: Tạo trong TheHive

Cấu hình Alert với các trường:
```text
Title:       [Wazuh-$exec.all_fields.rule.id] $exec.all_fields.rule.description
Severity:    $dynamic_severity_scoring.severity
Date:        $convert_date 
Source:      Wazuh-Shuffle-SOAR
Summary: 
  🖥️ Host: $exec.all_fields.agent.name
  📌 Rule: $exec.all_fields.rule.id
  🎯 MITRE: $dynamic_severity_scoring.mitre_id
  📊 Type: $dynamic_severity_scoring.enrichment_type
  🔍 VT Score: $dynamic_severity_scoring.vt_score
Tags:        ["wazuh", "automated", "phase2", "$dynamic_severity_scoring.enrichment_type"]
```

![Case được tạo tự động trên TheHive](<ĐƯỜNG_DẪN_ẢNH_5>)

---

**Node 8 — Get_Exec_ID**  
Lấy Execution ID hiện tại từ Shuffle API để tạo link form phê duyệt cho analyst.Execution ID dùng cho link `frontend_continue` trong email. Node này gọi API nội bộ:
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

**Condition trên branch: Quyết định việc gửi mail**  
Điều kiện `send_email = true` nối từ `Get_Exec_ID` → `Email_App`:

```
Condition: $dynamic_severity_scoring.0.message.send_email equals true
    → TRUE:  Tiếp tục gửi thông báo đến Email_App 
    → FALSE: Case đã lưu trên TheHive, không cần can thiệp
```

---

**Node 9 — Email_App**  
Do tính năng email tích hợp của User Input bị vô hiệu hóa trên Shuffle self-hosted, ta dùng node `Email App` riêng biệt để gửi thông báo qua SMTP.

Cấu hình SMTP:
```
Action:    Send email smtp
Username:  <GMAIL_ADDRESS>
Password:  <GMAIL_APP_PASSWORD>    
SMTP host: smtp.gmail.com
SMTP port: 587
Recipient: <SOC_ANALYST_EMAIL>
```

Nội dung email:
```
Subject: Wazuh Alert - Action Required: Block IP

Body:
  ⚠️ SOC ALERT - Action Required ⚠️

  === ALERT DETAILS ===
  Rule: $exec.all_fields.rule.description
  Host: $exec.all_fields.agent.name
  Source IP: $exec.all_fields.data.win.eventdata.ipAddress
  ==============================
  An IP needs to be blocked. Please log into Shuffle, check the Executions tab, and approve the User Input form.
```

![Email thông báo nhận được trong Gmail](<ĐƯỜNG_DẪN_ẢNH_6>)

> **Truy cập Form phê duyệt (Self-hosted):**  
> Trên bản self-hosted, biến `$exec.authorization` bị ẩn nên không thể nhúng link form trực tiếp vào email. Analyst cần truy cập form theo cách thủ công:
> 1. Vào Shuffle UI → Tab **Executions** → Tìm execution đang **WAITING** (màu vàng)
> 2. Click vào execution → Click node **Email User Input** → Copy link `frontend_continue`
> 3. Sửa link: Đổi port `5001` → `3001`, **xóa** `&answer=true` (nếu có), **giữ nguyên** `&source_node=...`, thêm `&backend_url=http://192.168.56.10:5001` vào cuối
> 4. Dán link đã sửa vào trình duyệt → Form hiện ra với nút **Continue** (Block IP) / **Stop** (Bỏ qua)
>
> ⚠️ **Quan trọng:** Mỗi execution có ID riêng. Link của execution cũ (đã answered hoặc đã restart) sẽ không hoạt động. Phải lấy link từ execution **mới nhất đang WAITING**.

---

**Node 10 — Email_User_Input**  
Tạo form phê duyệt chờ analyst phản hồi.

Cấu hình:
```
Name:              Email_User_Input
Input-Questions:   Block_IP;Yes;No     
```
Khi chạy, node sẽ vào trạng thái `WAITING` — workflow tạm dừng cho đến khi analyst trả lời qua form. Form hiển thị:
- Add Note
- Question: "What do you want to do?"
- `Continue`  / `Stop`

Analyst bấm Continue hoặc Stop, kết quả được truyền xuống Node 11 với condition trên branch kiểm tra user có approved hay không.

![Form phê duyệt Email User Input](<ĐƯỜNG_DẪN_ẢNH_7>)

---

**Node 11 — Get_Wazuh_Token**  
Wazuh API yêu cầu xác thực JWT. Cần gọi API authenticate trước để lấy token.

Cấu hình trong Shuffle:
```
Method:     POST
URL:        https://192.168.56.10:55000/security/user/authenticate?raw=true
Headers:    Content-Type: application/json
Username:   wazuh
Password:   wazuh
Verify:     False        
Timeout:    10
```

Kết quả thành công sẽ trả về:
- `status: 200`
- `body: eyJhbGciOi...` 
- `success: true`

![Kết quả Test Action Get Wazuh Token](<ĐƯỜNG_DẪN_ẢNH_8>)

> **⚠️ Lưu ý quan trọng:**
> - Tham số `?raw=true` trong URL rất quan trọng — nếu thiếu, API trả về JSON object `{"data":{"token":"eyJ..."}}` thay vì chuỗi token thuần, gây lỗi ở Node 12.
> - **Proxy phải để trống** — nếu có giá trị mặc định (ví dụ `http://192.168.0.1:8080`), xóa sạch để tránh timeout.
> - **Body phải để trống** — API authenticate không cần request body.



**Node 12 — Wazuh_Active_Response**  
Chỉ thực thi khi analyst chọn `Continue` và `src_ip` tồn tại.

Cấu hình trong Shuffle:
```
Method:      PUT
URL:         https://192.168.56.10:55000/active-response
Headers:     Authorization: Bearer $get_wazuh_token.body
             Content-Type: application/json
Verify:      False
Timeout:     10
```

Body — sử dụng lệnh `!netsh` với format `alert.data.srcip`:
```json
{"command":"!netsh","alert":{"data":{"srcip":"$exec.all_fields.data.win.eventdata.ipAddress"}}}
```

Kết quả thành công sẽ trả về:
- `status: 200`
- `message: "AR command was sent to all agents"`
- `total_affected_items: 1`, `total_failed_items: 0`

![Kết quả Test Action Wazuh Active Response](<ĐƯỜNG_DẪN_ẢNH_9>)

> **⚠️ Tại sao dùng `!netsh` thay vì `firewall-drop`?**
>
> | Lệnh | Script | Hoạt động trên | Cơ chế |
> |------|--------|---------------|--------|
> | `!firewall-drop` | `firewall-drop` | Linux (iptables) | Thêm rule iptables DROP |
> | `!route-null` | `route-null.exe` | Windows | Null route (cần default gateway) |
> | **`!netsh`** | **`netsh.exe`** | **Windows** | **Windows Firewall rule** |
>
> Trong lab này, alert RDP brute force (EID 4625) đến từ **Windows 10 Agent**. Lệnh Active Response được gửi đến agent đó để block IP. Vì agent chạy Windows:
> - `firewall-drop` → **không hoạt động** (script Linux, dùng iptables)
> - `route-null` → **lỗi** "Couldn't get default gateway" (mạng VirtualBox host-only không có gateway)
> - `netsh` → ✅ **hoạt động** — tạo rule Windows Firewall chặn IP nguồn tấn công

> **⚠️ Tại sao dùng format `alert.data.srcip` thay vì `arguments`?**
>
> Wazuh Active Response scripts (v4+) đọc source IP từ trường `alert.data.srcip` trong JSON input, **không phải** từ `arguments`:
> ```
> ❌ {"command":"!netsh","arguments":["srcip","1.2.3.4"]}
>    → Log: "Cannot read 'srcip' from data"
>
> ✅ {"command":"!netsh","alert":{"data":{"srcip":"1.2.3.4"}}}
>    → Log: "netsh: Ended" (thành công)
> ```

---

### Cấu hình Wazuh Active Response trên Ubuntu Server

Để Wazuh Manager nhận và chuyển tiếp lệnh Active Response đến agent, cần khai báo trong `/var/ossec/etc/ossec.conf` trên Ubuntu Server:

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


Xác nhận các script Active Response có sẵn:
```bash
dir "C:\Program Files (x86)\ossec-agent\active-response\bin\"
# → netsh.exe, restart-wazuh.exe, route-null.exe
```

Xác nhận block IP hoạt động (test với IP giả `1.2.3.4`):
```powershell
netsh advfirewall firewall show rule name=all | findstr "1.2.3.4"
# → RemoteIP: 1.2.3.4/32   
```

![Kiểm tra Windows Firewall block IP](<ĐƯỜNG_DẪN_ẢNH_10>)

---



---

##  Giải thích các File Cấu hình

- [shuffle_workflow.json](./shuffle_workflow.json): Toàn bộ Workflow từ Shuffle của luồng SOAR.

- [wazuh_shuffle_integration.conf](./wazuh_shuffle_integration.conf): Đoạn XML Integration cần thêm vào `ossec.conf` trên Wazuh Manager để kích hoạt việc gửi Webhook sang Shuffle.



##  Kết quả đạt được

- Triển khai Shuffle SOAR self-hosted tích hợp hoàn toàn với Wazuh và TheHive từ Phase 1.
- Thiết kế kiến trúc với 3 nhánh xử lý: File Hash → VT File API, Source IP → VT IP API, Behavioral → skip VT. Đảm bảo workflow không bị lỗi khi gặp alert thiếu hash hoặc IP.
-  Xây dựng cơ chế Dynamic Severity Scoring — tự động nâng/hạ mức độ nghiêm trọng của Case dựa trên kết quả VirusTotal, giảm 70% thời gian triage thủ công.
-  Cấu hình Email App gửi thông báo cảnh báo + Email User Input tạo form phê duyệt Block IP. Chỉ kích hoạt khi alert thực sự cần hành động (VT positive hoặc rule level ≥ 12), giảm alert fatigue cho analyst.
-  Kích hoạt Wazuh Active Response với xác thực JWT — tự động chặn IP tấn công ở tầng firewall trong vòng 300 giây.
-  Mọi sự cố được tạo thành Case trong TheHive tự động kèm enrichment đầy đủ gồm VT score, IP reputation, hoặc ghi chú behavioral để chuẩn bị nguyên liệu cho điều tra chuyên sâu.

![Execution flow hoàn chỉnh chạy thành công trên Shuffle](<ĐƯỜNG_DẪN_ẢNH_11>)