# 🎯 Windows 10 Telemetry Setup (Sysmon & Wazuh Agent)

Mục tiêu của bước này là biến máy tính Windows thông thường thành một "cảm biến" thu thập dữ liệu hành vi chuyên sâu (Telemetry) và liên tục đẩy về SIEM trung tâm tại Ubuntu Server (192.168.56.10).

## 1. Cài đặt Sysmon với bộ cấu hình SwiftOnSecurity
Windows Event Log mặc định rất hạn chế. Sysmon sẽ giúp bắt được các hành vi như: Process Creation, Network Connection, và Driver Load.

- Tải công cụ: - Tải Sysmon từ bộ Sysinternals Suite.

  - Tải file cấu hình chuẩn [tại đây](../Phase-2-Detection/sysmonconfig.xml)


Cài đặt: Mở PowerShell quyền Admin, di chuyển vào thư mục chứa Sysmon và chạy lệnh:

```bash
.\Sysmon64.exe -i sysmonconfig.xml 
```
Sau khi chạy, Sysmon sẽ bắt đầu ghi log vào Event Viewer.

## 2. Cài đặt Wazuh Agent và Kết nối 
Sau khi đã có log Sysmon, chúng ta cần Wazuh Agent để chuyển log về Ubuntu Server.

- Cấu hình đẩy log Sysmon :

  - Chỉnh sửa file C:\Program Files (x86)\ossec-agent\ossec.conf.Bạn có thể xem chi tiết [tại đây](../Phase-2-Detection/ossec.conf) 

- Lưu file và thực hiện Restart service Wazuh để áp dụng cấu hình mới

## 3. Kiểm tra và Xác nhận 
Đây là bước cuối cùng để đảm bảo đường ống dữ liệu không bị tắc.

- Trên Windows 10: Kiểm tra xem các sự kiện có đang sinh ra liên tục không.
- Trên Wazuh Dashboard: 
  - Vào mục Agents, xác nhận máy Windows 10 ở trạng thái Active.
  - Vào Security Events, xác nhận log từ Windows đã đổ về SIEM.




