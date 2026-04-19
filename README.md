# 🛡️ End-to-End SOC Automation & Incident Response Lab
---
Dự án này mô phỏng một hệ thống SOC, tích hợp khả năng giám sát, tự động hóa phản ứng và quản lý sự cố.
## Module 2: Triển khai SIEM, EDR và Thu thập Telemetry
---

Mục tiêu: Thiết lập luồng thu thập dữ liệu (Telemetry) chuyên sâu từ máy trạm Windows, tập trung quản lý qua SIEM/EDR, và chuẩn bị nền tảng hệ thống Ticketing để phục vụ cho công tác tự động hóa (SOAR) ở giai đoạn sau.

### 🏗️ Kiến trúc Hệ thống 
Hệ thống được vận hành trên 2 máy ảo chính:

1.Ubuntu Server: Đóng vai trò là máy chủ trung tâm.

- Chạy Wazuh Manager (Cài đặt Native) để quản lý SIEM/EDR.

- Chạy TheHive (Cài đặt qua Docker) phục vụ quản lý sự cố .

2.Windows 10: Đóng vai trò là máy trạm mục tiêu.

- Chạy Sysmon (cấu hình SwiftOnSecurity) để sinh log chi tiết.

- Chạy Wazuh Agent để thu thập và đẩy log về Ubuntu Server.

### Các bước Triển khai Chi tiết
**Bước 1**: Chuẩn bị trên Windows 10 
Thay vì chỉ phụ thuộc vào Windows Event Log mặc định, hệ thống được tăng cường khả năng giám sát hành vi bằng Sysmon.

- Thao tác: Cài đặt Sysmon trên Windows 10 kết hợp với bộ ruleset của SwiftOnSecurity.

- Mục đích: Bắt giữ chi tiết các hành vi tạo tiến trình (Process Creation), thay đổi file, kết nối mạng và mã Hash của các tệp thực thi (MD5, SHA256) – những dữ liệu sống còn để phát hiện mã độc.

Bước 2: Triển khai SIEM/EDR Trung tâm (Wazuh Native)
Hệ thống được cài đặt Native trên Linux để tối ưu hóa tài nguyên và kiểm soát sâu cấu hình hệ điều hành.

- Thao tác: Cài đặt Wazuh Manager, Wazuh Indexer và Wazuh Dashboard trực tiếp lên Ubuntu Server.

- Mục đích: Xây dựng bộ não trung tâm tiếp nhận, phân tích, lập chỉ mục và hiển thị trực quan các cảnh báo an ninh.

Bước 3: Triển khai Hệ thống Quản lý Sự cố (TheHive Docker)
- Thao tác: Sử dụng docker-compose để triển khai TheHive và cơ sở dữ liệu Cassandra/Elasticsearch trên cùng máy Ubuntu. Cấu hình mở port 9000.

- Mục đích: Cung cấp nền tảng Ticketing & Case Management. Chuẩn bị sẵn tài khoản Service và API Key để tích hợp SOAR trong tương lai.

Bước 4: Kết nối Agent và Cấu hình Đổ Log (Log Ingestion)
- Thao tác trên Windows 10: Cài đặt Wazuh Agent, trỏ IP về Ubuntu Server.

- Cấu hình ossec.conf (Agent): Khai báo thẻ <localfile> để chỉ định Agent đọc log từ 3 nguồn chính:

  - Application 

  - Security 

  - Microsoft-Windows-Sysmon/Operational 

Bước 5: Cấu hình Mở rộng trên Manager (Chuẩn bị cho Automation)
Để hệ thống SOAR có dữ liệu thô hoạt động, SIEM cần được cấu hình lưu trữ toàn bộ sự kiện.

- Thao tác trên Ubuntu: 1. Mở file /var/ossec/etc/ossec.conf trên Manager.
2. Chuyển đổi <logall_json>no</logall_json> thành <logall_json>yes</logall_json>.
3. Mở file /etc/filebeat/filebeat.yml và kích hoạt module archives: enabled: true.

- Kết quả: Wazuh bắt đầu lưu trữ toàn bộ dữ liệu thô định dạng JSON vào file archives.json, sẵn sàng làm đầu vào cho nền tảng SOAR.

Bước 6: Giả lập Tấn công Tự động (Attack Simulation với Atomic Red Team)
Thay vì tấn công thủ công, dự án áp dụng phương pháp giả lập tiêu chuẩn để kiểm chứng năng lực phát hiện.

- Thao tác: Triển khai framework Atomic Red Team (ART) trên máy Windows 10.

- Thực thi: Khởi chạy các kịch bản PowerShell tự động để giả lập các chiến thuật tấn công trong khung MITRE ATT&CK. Cụ thể:

  - Kỹ thuật T1003 (OS Credential Dumping): Giả lập hành vi trích xuất mật khẩu từ bộ nhớ (tương tự Mimikatz).

  - Kỹ thuật T1059 (Command and Scripting Interpreter): Giả lập thực thi mã độc qua PowerShell.

Bước 7: Phân tích Log và Tinh chỉnh Quy tắc Phát hiện 
Đây là bước cốt lõi chứng minh năng lực phân tích của một SOC Analyst.

- Thao tác: 
  1.Phân tích các log kiện từ Sysmon (Event ID 1, 8, 10) sinh ra sau khi chạy Atomic Red Team.
  2.Truy cập máy Ubuntu, mở file /var/ossec/etc/rules/local_rules.xml của Wazuh.
  3.Viết các Custom Rules (Luật tùy chỉnh) dựa trên biểu thức chính quy (Regex) và mã Hash để hệ thống nhận diện chính xác các hành vi của ART.

- Mục đích: Khớp nối cảnh báo của hệ thống (Alert) trực tiếp vào các mã kỹ thuật của MITRE ATT&CK.
