# 🔬 Phase 3: Quản lý Sự cố & Báo cáo Điều tra (DFIR)

Nếu Phase 1 là "Phát hiện" và Phase 2 là "Tự động hóa", thì Phase 3 là giai đoạn **con người vào cuộc** — mô phỏng công việc thực tế của một SOC Analyst khi tiếp nhận, điều tra và đóng một sự cố hoàn chỉnh.

Các Case trong TheHive đã được Shuffle tự động tạo ra từ Phase 2 với đầy đủ ngữ cảnh (cảnh báo Wazuh + kết quả VirusTotal). Phase 3 tập trung vào việc **điều tra chuyên sâu** những Case đó bằng Cortex, và xuất ra **Incident Report chuyên nghiệp** theo chuẩn SOC thực tế.

---

## 🧩 Công cụ sử dụng

- **TheHive** *(đã triển khai ở Phase 1, đã có Case từ Phase 2)*: Nền tảng quản lý vòng đời sự cố. Analyst thực hiện toàn bộ quy trình điều tra, gắn nhãn, phân công và đóng Case ngay trong giao diện này.

- **Cortex**: Engine phân tích IOC (Indicator of Compromise) tích hợp trực tiếp với TheHive. Cho phép chạy hàng chục **Analyzer** tự động (VirusTotal, AbuseIPDB, Shodan, MISP...) trên một IOC chỉ bằng một cú click — thay vì tra cứu thủ công từng trang web.

---

## 🔄 Vòng đời Sự cố (Incident Lifecycle)

```
[Phase 2 đầu ra] Case tự động trong TheHive
    │
    ▼
Phase 3 bắt đầu:

[Bước 1] Tiếp nhận Alert
    → Analyst xem xét Alert do Shuffle tạo
    → Nâng cấp từ Alert thành Case nếu cần điều tra

[Bước 2] Phân tích IOC với Cortex
    → Gửi IP, Hash, Domain sang Cortex Analyzers
    → Kết quả trả về ngay trong TheHive Task

[Bước 3] Xây dựng Timeline
    → Ghép nối log từ Wazuh + kết quả Cortex
    → Xác định: Ai? Máy nào? Lúc mấy giờ? Kỹ thuật gì (MITRE ID)?

[Bước 4] Ghi nhận IOCs
    → Thêm Observables vào Case: IP, Hash, Process name, Registry key

[Bước 5] Đóng Case & Viết Incident Report
    → Điền đầy đủ: Summary, Timeline, IOCs, Remediation
    → Xuất PDF / Markdown
```

---

## ⚙️ Triển khai Cortex

### Bước 1 — Cài đặt Cortex bằng Docker

Cortex chạy song song TheHive trên cùng máy Ubuntu. Thêm service Cortex vào file `docker-compose.yml` hiện có (đã tạo ở Phase 1):

```yaml
  cortex:
    image: thehiveproject/cortex:latest
    ports:
      - "9001:9001"
    environment:
      - job_directory=/tmp/cortex-jobs
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/cortex-jobs:/tmp/cortex-jobs
    depends_on:
      - elasticsearch
```

Khởi động lại stack:
```bash
sudo docker-compose down
sudo docker-compose up -d
```

Truy cập Cortex tại: `http://192.168.56.10:9001`

---

### Bước 2 — Cấu hình Cortex Analyzers

Sau khi đăng nhập Cortex lần đầu, tạo Organization và kích hoạt các Analyzer miễn phí:

| Analyzer | Phân tích loại IOC | API Key cần thiết |
|---|---|---|
| VirusTotal_GetReport | File Hash, IP, URL | VirusTotal (free) |
| AbuseIPDB | IP độc hại | AbuseIPDB (free) |
| Shodan_Host | IP, mở port nào | Shodan (free tier) |
| MISP_2_1 | Hash, IP, Domain | MISP instance |

Vào **Organization → Analyzers → Enable** để kích hoạt từng Analyzer, điền API Key tương ứng.

---

### Bước 3 — Kết nối TheHive với Cortex

Trong TheHive, vào **Admin → Cortex** và thêm:
- URL: `http://192.168.56.10:9001`
- API Key: Tạo trong Cortex tại **Organization → API Keys**

Sau khi kết nối, mỗi Observable trong TheHive Case sẽ có nút **"Run Analyzers"** để gửi thẳng sang Cortex phân tích.

---

## 🕵️ Case Study: Điều tra 5 Kịch bản Tấn công

Mỗi kịch bản được giả lập bằng Atomic Red Team (đã cấu hình ở Phase 1), phát sinh Case tự động qua Shuffle (Phase 2), và được điều tra đầy đủ tại đây.

### Kịch bản 1 — T1003: OS Credential Dumping

**Mô phỏng:** Chạy Atomic Red Team T1003 trên Windows 10.

**IOCs thu thập:**
- Process: `lsass.exe` bị truy cập bởi tiến trình không phải hệ thống
- File: `lazagne.exe` hoặc `mimikatz.exe`
- Event ID: `4656` (Handle to Object), `4663` (Object Access)

**Cortex Analyzers chạy:**
- VirusTotal: Kiểm tra hash của file thực thi
- AbuseIPDB: Kiểm tra IP C2 nếu có kết nối ra ngoài

---

### Kịch bản 2 — T1059.001: PowerShell Execution

**Mô phỏng:** Chạy Atomic Red Team T1059.001 — thực thi lệnh PowerShell encoded.

**IOCs thu thập:**
- CommandLine: `powershell.exe -EncodedCommand <base64>`
- Event ID Sysmon: `1` (Process Create), `3` (Network Connection)

---

### Kịch bản 3 — T1547: Registry Run Key Persistence

**Mô phỏng:** Atomic Red Team T1547.001 — tạo Registry key để tự khởi động.

**IOCs thu thập:**
- Registry path: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`
- Event ID Sysmon: `13` (Registry Value Set)

---

### Kịch bản 4 — T1021: Remote Services (Lateral Movement)

**Mô phỏng:** Atomic Red Team T1021 — kết nối RDP/SMB bất thường.

**IOCs thu thập:**
- IP nguồn bất thường
- Event ID: `4624` (Logon Success), `4625` (Logon Failure)

---

### Kịch bản 5 — T1070: Indicator Removal (Log Clearing)

**Mô phỏng:** Atomic Red Team T1070.001 — xóa Windows Event Log.

**IOCs thu thập:**
- Event ID: `1102` (Audit log cleared), `104` (System log cleared)

---

## 📄 Cấu trúc Incident Report

Mỗi Case được xuất thành một bản báo cáo theo cấu trúc chuẩn NIST/SANS:

```markdown
# INCIDENT REPORT — [Tên kịch bản]

## 1. Executive Summary
Tóm tắt ngắn gọn: Chuyện gì xảy ra? Mức độ nghiêm trọng? Đã xử lý chưa?

## 2. Incident Details
- Ngày giờ phát hiện:
- Hệ thống bị ảnh hưởng:
- MITRE ATT&CK Technique:
- Severity:

## 3. Timeline
| Thời gian | Sự kiện |
|---|---|
| HH:MM | Wazuh phát hiện alert |
| HH:MM | Shuffle tạo Case trong TheHive |
| HH:MM | Analyst bắt đầu điều tra |
| HH:MM | Cortex xác nhận IOC độc hại |
| HH:MM | Block IP / Cô lập máy |
| HH:MM | Case đóng |

## 4. Indicators of Compromise (IOCs)
| Loại | Giá trị | Nguồn xác nhận |
|---|---|---|
| File Hash | abc123... | VirusTotal (45/72 engines) |
| IP Address | 103.x.x.x | AbuseIPDB (score: 100) |
| Process | lazagne.exe | Wazuh Rule 100002 |

## 5. Root Cause Analysis
Phân tích nguyên nhân gốc rễ: Tại sao cuộc tấn công xảy ra được?

## 6. Remediation Actions
- [ ] Block IP tại firewall
- [ ] Xóa file độc hại khỏi endpoint
- [ ] Reset mật khẩu tài khoản bị ảnh hưởng
- [ ] Vá lỗ hổng liên quan

## 7. Lessons Learned
Điều gì cần cải thiện trong Detection Rules, Playbook hoặc quy trình?
```

---

## 📂 Giải thích các File

- [incident_report_template.md](./incident_report_template.md): Template báo cáo điều tra chuẩn hóa, dùng cho tất cả 5 kịch bản Case Study.

- [case_studies/](./case_studies/): Thư mục chứa 5 Incident Report hoàn chỉnh tương ứng với 5 kịch bản tấn công đã điều tra.

---

## 📚 Tham chiếu

- **TheHive** đã triển khai: [02-TheHive-Docker-Deployment.md](../docs/02-TheHive-Docker-Deployment.md)
- **Cases nguồn** được tạo tự động bởi Shuffle: [Phase-2-Automation](../Phase-2-Automation/README.md)
- **Kịch bản tấn công** được giả lập bằng Atomic Red Team: [Phase-1-Detection](../Phase-1-Detection/README.md)

---

## 🎯 Kết quả đạt được

- ✅ Triển khai **Cortex** tích hợp TheHive với **10+ Analyzers** tự động hóa phân tích IOC.
- ✅ Quản lý **20+ ticket sự cố** trên TheHive, bao gồm toàn bộ vòng đời từ Alert → Investigation → Closure.
- ✅ Thực hiện điều tra chuyên sâu và viết **5 Incident Report hoàn chỉnh** cho 5 kịch bản tấn công thực tế theo khung MITRE ATT&CK.
- ✅ Chứng minh khả năng **truy vết toàn bộ chuỗi tấn công** (Kill Chain) từ log thô Wazuh đến IOCs được xác thực bởi Cortex.
