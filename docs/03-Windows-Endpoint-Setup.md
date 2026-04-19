# 🎯 Windows 10 Telemetry Setup (Sysmon & Wazuh Agent)

Mục tiêu của bước này là biến máy tính Windows thông thường thành một "cảm biến" thu thập dữ liệu hành vi chuyên sâu và liên tục đẩy về SIEM trung tâm.

## 1. Cài đặt Sysmon với bộ cấu hình SwiftOnSecurity
Windows Event Log mặc định không đủ để bắt các kỹ thuật tấn công hiện đại. Sysmon  sẽ khắc phục điều này.

- Tải bộ công cụ **Sysinternals Suite** từ Microsoft.
- Tải file cấu hình tiêu chuẩn công nghiệp từ GitHub: [SwiftOnSecurity Sysmon Config](https://github.com/SwiftOnSecurity/sysmon-config).
- Mở PowerShell với quyền Administrator và chạy lệnh cài đặt:
```powershell
sysmon64.exe -accepteula -i sysmonconfig-export.xml
```
## 2. Cài đặt Wazuh Agent và trỏ IP
- Tải file .msi của Wazuh Agent tương ứng với phiên bản Manager từ trang chủ Wazuh.

- Cài đặt qua giao diện UI hoặc chạy lệnh PowerShell:

```bash
msiexec.exe /i wazuh-agent.msi /q WAZUH_MANAGER="<IP_UBUNTU_SERVER>" WAZUH_REGISTRATION_SERVER="<IP_UBUNTU_SERVER>"
```
- Mở file cấu hình Agent tại C:\Program Files (x86)\ossec-agent\ossec.conf. Thêm đoạn mã sau để Agent biết cách đọc log của Sysmon:

```bash
<localfile>
  <location>Microsoft-Windows-Sysmon/Operational</location>
  <log_format>eventchannel</log_format>
</localfile>
```
- Restart lại service Wazuh từ mục Services.msc của Windows.

## 3. Kiểm tra Telemetry
- Trên Endpoint: Mở Event Viewer -> Applications and Services Logs -> Microsoft -> Windows -> Sysmon -> Operational. Bạn sẽ thấy log chi tiết về Process (Event ID 1) hoặc Network (Event ID 3) liên tục được sinh ra.

- Trên Server: Đăng nhập Wazuh Dashboard, vào mục Agents để xác nhận kết nối.


