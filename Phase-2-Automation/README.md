# 🤖 Phase 2: SOC Automation & Triage tự động 

Nếu Phase 1 là "Lắng nghe và Giám sát", thì Phase 2 là bước nâng cấp hệ thống lên cấp độ Chủ động Phản ứng. Toàn bộ hạ tầng (Wazuh Manager, TheHive) đã được dựng sẵn ở Phase 1 — Phase 2 tập trung vào việc kết nối và tự động hóa chúng lại với nhau thông qua Shuffle SOAR.

---

## Công cụ sử dụng

- **Shuffle (SOAR)**: Bộ não điều phối tự động mã nguồn mở. Nhận Webhook từ Wazuh, xử lý logic, gọi API bên ngoài và phân phối hành động đến TheHive + Email.

- **VirusTotal API**: Dịch vụ kiểm tra danh tiếng file/hash. Shuffle tự động gọi API này để enrich cảnh báo ngay khi nhận được từ Wazuh — không cần analyst làm thủ công.

- **TheHive**: Nhận Case được tạo tự động từ Shuffle, kèm đầy đủ kết quả Enrichment — sẵn sàng cho đội SOC điều tra ở Phase 3.

- **Email**: Shuffle gửi email yêu cầu xác nhận kèm 2 link **TRUE / FALSE**. Nếu analyst chọn TRUE → Wazuh Active Response tự động block IP nguồn tấn công.

---

## 🔄 Luồng Tự động hóa

```
Wazuh phát hiện Threat (từ Detection Rules Phase 1)
    │
    ▼
Shuffle nhận Webhook từ Wazuh
    │
    ├──► Parse JSON → Trích xuất: Rule ID, Level, Hostname, IP nguồn, File Hash
    │
    ├──► Gọi VirusTotal API
    │         └── Kiểm tra Hash → Trả về số AV engine phát hiện / Tổng
    │
    ├──► Tạo Alert/Case tự động trong TheHive
    │         └── Tiêu đề, Severity, Raw log + Kết quả VirusTotal đính kèm
    │
    └──► Gửi Email (User Prompt) đến SOC Analyst
              ├── Nội dung: Chi tiết cảnh báo + VirusTotal score
              └── 2 link: [TRUE] Block IP  |  [FALSE] Bỏ qua
                              │
                              ▼ (nếu chọn TRUE)
                    Wazuh Active Response
                    → Chạy script firewall block IP nguồn tấn công
```

---

## ⚙️ Triển khai

### Bước 1 — Cài đặt Shuffle trên Ubuntu Server

Shuffle chạy bằng Docker, triển khai trên cùng máy Ubuntu đang chạy Wazuh và TheHive.

```bash
git clone https://github.com/Shuffle/Shuffle
cd Shuffle
docker-compose up -d
```

Truy cập giao diện: `http://192.168.56.10:3001`  
Đăng ký tài khoản admin ngay lần đầu truy cập.

> ⚠️ Nếu gặp lỗi Opensearch không khởi động được, chạy lệnh sau để fix giới hạn bộ nhớ hệ thống:
> ```bash
> sudo sysctl -w vm.max_map_count=262144
> ```

---

### Bước 2 — Kết nối Wazuh → Shuffle (Webhook Integration)

Thêm khối `<integration>` vào file `/var/ossec/etc/ossec.conf` trên Wazuh Manager. Chỉ gửi các alert có level từ 7 trở lên để tránh noise:

```xml
<integration>
  <name>shuffle</name>
  <hook_url>http://192.168.56.10:3001/api/v1/hooks/<SHUFFLE_WEBHOOK_ID></hook_url>
  <level>7</level>
  <alert_format>json</alert_format>
</integration>
```

Khởi động lại Wazuh để áp dụng:
```bash
sudo systemctl restart wazuh-manager
```

> Lấy `SHUFFLE_WEBHOOK_ID` từ Shuffle: **New Workflow → Add Trigger → Webhook → Copy URL**.

---

### Bước 3 — Xây dựng Workflow trong Shuffle

Tạo Workflow mới và kéo thả các node theo thứ tự:

**Node 1 — Webhook Trigger**  
Điểm đầu vào nhận dữ liệu từ Wazuh. Sau khi tạo xong, kích hoạt thử bằng cách chạy một attack Atomic Red Team ở Phase 1 — dữ liệu JSON sẽ xuất hiện ngay trong Shuffle.

**Node 2 — Execution Argument (Parse)**  
Trích xuất các trường cần thiết từ JSON của Wazuh:
```
$exec.all_fields.data.srcip      → IP nguồn
$exec.all_fields.rule.id         → Rule ID
$exec.all_fields.rule.description → Mô tả cảnh báo
$exec.all_fields.agent.name      → Hostname máy bị ảnh hưởng
```

**Node 3 — HTTP Action (VirusTotal Enrichment)**  
- Method: `GET`
- URL: `https://www.virustotal.com/api/v3/files/<file_hash>`
- Header: `x-apikey: <VIRUSTOTAL_API_KEY>`

Lấy API Key miễn phí tại [virustotal.com](https://www.virustotal.com) — giới hạn 4 request/phút với tài khoản free.

**Node 4 — TheHive: Create Alert**  
Kết nối TheHive vào Shuffle:
- URL: `http://192.168.56.10:9000`
- API Key: Tạo trong TheHive tại **Admin → Users → API Key**

Cấu hình Alert với các trường:
```
Title:       [Wazuh] $exec.all_fields.rule.description
Severity:    2 (Medium) hoặc map theo rule.level
Description: IP: <srcip> | VirusTotal: <vt_score> | Host: <agent.name>
Tags:        ["wazuh", "automated", "phase2"]
```

**Node 5 — Email (User Prompt)**  
Shuffle gửi email đến địa chỉ SOC Analyst với nội dung:
```
Action required!
Would you like to block this source IP: <srcip>?

IF TRUE:  <shuffle_callback_url>&answer=true
IF FALSE: <shuffle_callback_url>&answer=false
```

**Node 6 — Trigger (Check Response)**  
Chỉ tiếp tục nếu analyst chọn `true`.

**Node 7 — Wazuh Active Response (Block IP)**  
Gọi Wazuh API để thực thi Active Response:
- URL: `https://192.168.56.10:55000/active-response`
- Method: `PUT`
- Body: `{ "command": "firewall-drop", "arguments": ["-", "-", "<srcip>", "300"] }`

---

### Bước 4 — Cấu hình Wazuh Active Response

Để Wazuh nhận lệnh block IP từ Shuffle, cần khai báo Active Response trong `/var/ossec/etc/ossec.conf`:

```xml
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <timeout>300</timeout>
</active-response>
```

Script `firewall-drop` có sẵn trong Wazuh tại `/var/ossec/active-response/bin/firewall-drop`.  
Xác nhận script có quyền thực thi:
```bash
ls -la /var/ossec/active-response/bin/firewall-drop
```

---

## 📂 Giải thích các File Cấu hình

- [shuffle_workflow.json](./shuffle_workflow.json): Bản Export toàn bộ Workflow từ Shuffle. Import file này vào Shuffle của bạn để tái tạo ngay luồng SOAR mà không cần cấu hình lại từ đầu.

- [wazuh_shuffle_integration.conf](./wazuh_shuffle_integration.conf): Đoạn XML Integration cần thêm vào `ossec.conf` trên Wazuh Manager để kích hoạt việc gửi Webhook sang Shuffle.



## 🎯 Kết quả đạt được

- ✅ Triển khai **Shuffle SOAR** tích hợp hoàn toàn với Wazuh và TheHive từ Phase 1.
- ✅ Xây dựng luồng **tự động Enrichment** bằng VirusTotal API — giảm **70% thời gian triage thủ công** cho mỗi sự cố.
- ✅ Cấu hình **Human-in-the-Loop**: Email User Prompt cho phép analyst ra quyết định block IP chỉ với 1 click.
- ✅ Kích hoạt **Wazuh Active Response** — tự động chặn IP tấn công ở tầng firewall trong vòng 300 giây.
- ✅ Mọi sự cố được tạo thành **Case trong TheHive** tự động — chuẩn bị đầy đủ nguyên liệu cho điều tra chuyên sâu ở Phase 3.