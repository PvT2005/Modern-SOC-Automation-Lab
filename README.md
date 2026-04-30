# 🛡️ End-to-End SOC Automation & Incident Response Lab
---
Dự án này mô phỏng một hệ thống SOC, tích hợp khả năng giám sát, tự động hóa phản ứng và quản lý sự cố.
## Module 2: Triển khai SIEM, EDR và Thu thập Telemetry
---

Mục tiêu: Thiết lập luồng thu thập dữ liệu (Telemetry) chuyên sâu từ máy trạm Windows, tập trung quản lý qua SIEM/EDR, và chuẩn bị nền tảng hệ thống Ticketing để phục vụ cho công tác tự động hóa (SOAR) ở giai đoạn sau.

### 🏗️ Architecture (Kiến trúc)
Dự án vận hành trên mô hình 2 thành phần chính:

SOC Brain (Ubuntu): Wazuh Manager & TheHive.

Target Machine (Windows 10): Sysmon & Wazuh Agent.

🚀 Implementation Steps (Các bước triển khai)
**Step 1**: Telemetry Generation with Sysmon
Tăng cường khả năng giám sát bằng Sysmon thay vì log mặc định.

- [Cài đặt và cấu hình Sysmon](./docs/03-Windows-Endpoint-Setup.md).



**Step 2**: SIEM/EDR Core (Wazuh Native)
Thiết lập bộ não trung tâm để thu thập và phân tích cảnh báo.

- Triển khai Wazuh Manager, Indexer và Dashboard trực tiếp trên Ubuntu.

- [Cài đặt Wazuh Native](./docs/01-Wazuh-Manager-Installation.md)

**Step 3**: Case Management (TheHive Docker)
Xây dựng nền tảng quản lý sự cố và Ticketing.

- Triển khai TheHive qua Docker Compose để sẵn sàng tích hợp SOAR.

- [Cài đặt TheHive & Docker](./docs/02-TheHive-Docker-Deployment.md)

**Step 4**: Log Ingestion Configuration
Cấu hình Agent để đọc dữ liệu từ Application, System, Security và Sysmon.

- Xem file cấu hình [wazuh_agent_ossec.conf](./Phase-2-Detection/wazuh_agent_ossec.conf) 

**Step 5**: Automation Readiness
Kích hoạt archives.json để lưu trữ dữ liệu thô phục vụ cho SOAR Playbooks.

- Action: Chỉnh sửa cấu hình Manager để xuất log dạng JSON.

**Step 6**: Attack Simulation (Atomic Red Team)
Giả lập tấn công theo khung MITRE ATT&CK (T1003 & T1059) để kiểm thử hệ thống.

- Action: Chạy các kịch bản PowerShell tự động trích xuất mật khẩu.

**Step 7**: Detection Rules Engineering
Viết các luật tùy chỉnh dựa trên phân tích log sự kiện thực tế.

- Technical Asset: Bộ luật phát hiện tùy chỉnh (local_rules.xml)