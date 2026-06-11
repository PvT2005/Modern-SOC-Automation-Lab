# Phase 1: Lắng nghe, Giám sát và Phát hiện Mối đe dọa

Thiết lập nền tảng giám sát toàn diện — từ thu thập Telemetry chuyên sâu trên Endpoint đến phân tích, phát hiện và quản lý cảnh báo theo khung MITRE ATT&CK.

Giai đoạn này triển khai kiến trúc SIEM với bộ Detection Rules tùy chỉnh. Tại đây, mọi sự kiện, luồng mạng và hành vi trên máy trạm sẽ được tổng hợp, phân tích dựa trên các luật cảnh báo để chỉ mặt đặt tên các rủi ro bảo mật trước khi chúng gây hại lớn hơn.



## Công cụ sử dụng

- **Wazuh**: Đóng vai trò là trung tâm "Thu thập và Phân tích". Thu nhận log, chạy đối chiếu với thư viện luật và đánh giá các hành vi bất thường.

- **Sysmon**: Đóng vai trò giám sát sâu trên Windows. Theo dõi mọi hành động khởi tạo tiến trình, chỉnh sửa Registry hay kết nối mạng và báo cáo lại với độ chi tiết vượt trội so với Windows Event Log mặc định.

- **Atomic Red Team**: Bộ công cụ kiểm thử mã nguồn mở ánh xạ trực tiếp với khung MITRE ATT&CK. Dùng để giả lập các kỹ thuật tấn công thực tế trên máy trạm Windows mục tiêu nhằm xác thực khả năng phát hiện của hệ thống.



## Luồng hoạt động

- **Telemetry Collection**: Sysmon và Windows Event Logs túc trực trên Windows Endpoint ghi nhận từng hành vi nhỏ nhất. Trình Wazuh Agent liên tục đóng gói các sự kiện này và đẩy về máy chủ Wazuh trung tâm.

- **Attack Simulation**: Atomic Red Team thực thi các kịch bản tấn công được lập trình sẵn theo từng Technique ID của MITRE ATT&CK. Đây là bước tạo ra sự kiện để xây dựng và kiểm thử Detection Rules.

- **Analysis & Detection**: Wazuh Manager tiếp nhận và bắt đầu bóc tách, chuẩn hóa dữ liệu log. Hệ thống đối chiếu với bộ luật tùy chỉnh. Nếu mFột tiến trình thỏa mãn điều kiện nghi ngờ, hệ thống lập tức kích hoạt cảnh báo.

- **Alerting**: Cảnh báo được ghi nhận trên Wazuh Dashboard kèm chi tiết đầy đủ về Rule ID, mức độ nghiêm trọng, thông tin máy trạm bị ảnh hưởng và ánh xạ MITRE ATT&CK. Đây là đầu ra của Phase 1, sẵn sàng chuyển tiếp sang Phase 2 qua Webhook.


## Quy trình thực hiện

1. Giả lập tấn công bằng Atomic Red Team trên máy Windows mục tiêu.

| MITRE ID | Tên kỹ thuật | Công cụ giả lập | Rule ID | 
|---|---|---|---|
| T1003.001 | OS Credential Dumping: LSASS Memory | Atomic Red Team | 100001–100002 | 
| T1059.001 | PowerShell Encoded / Bypass Execution | Atomic Red Team | 100010–100012 | 
| T1547.001 | Registry Run Keys / Startup Folder | Atomic Red Team | 100020–100021 |
| T1053.005 | Scheduled Task — Shell Payload | Atomic Red Team | 100030–100032 | 
| T1136.001 | Create Local Admin Account | Atomic Red Team | 100040–100041 | 
| T1110.001 | Brute Force Password Guessing | Script | 100050–100053 | 
| T1021.002 | Lateral Movement via SMB / PsExec | PsExec | 100060–100061 | 
| T1055.001 | Process Injection — DLL Injection | Atomic Red Team | 100070–100073 | 
| T1070.001 | Indicator Removal: Clear Event Logs | Atomic Red Team | 100080–100082 | 
| T1218.011 | LOLBas: Rundll32 Abuse | Atomic Red Team | 100090–100091 | 
| T1105 | Ingress Tool Transfer (certutil/bitsadmin) | Atomic Red Team | 100100–100101 | 
| T1082 | System Information Discovery / Recon | Atomic Red Team | 100110–100114 | 
| T1027 | Obfuscated Files / Payload Deobfuscation | Atomic Red Team | 100120–100122 |

2. Quan sát log thô đổ về Wazuh Dashboard 
3. Viết Detection Rule tùy chỉnh vào [local_rules.xml](./local_rules.xml) chứa toàn bộ 36 Detection Rules tùy chỉnh (Rule ID `100001`–`100122`) ánh xạ trực tiếp với 13 kỹ thuật tấn công theo khung MITRE ATT&CK. Bao gồm các cơ chế: single-event matching, threshold-based detection (`frequency`/`timeframe`), và process-chain correlation (parent → child process).
![rule](../screenshots/Wazuh_detection_rules.jpg)
4. Kiểm thử lại bằng cách tái giả lập tấn công 
```
Invoke-AtomicTest T1082 -TestNumbers 1
Invoke-AtomicTest T1059.001 -TestNumbers 1 
Invoke-AtomicTest T1547.001 -TestNumbers 1
Invoke-AtomicTest T1053.005 -TestNumbers 1
Invoke-AtomicTest T1136.001 -TestNumbers 8
Invoke-AtomicTest T1003.001 -TestNumbers 1
Invoke-AtomicTest T1055.001 -TestNumbers 2 
Invoke-AtomicTest T1218.011 -TestNumbers 1
Invoke-AtomicTest T1105 -TestNumbers 7 
Invoke-AtomicTest T1027 -TestNumbers 2 
1..10 | ForEach-Object { net use \\127.0.0.1\IPC$ /user:fakeuser "WrongPass$_" 2>$null; Start-Sleep -Milliseconds 500 }
& "$env:TEMP\PsExec.exe" -accepteula \\127.0.0.1 cmd.exe /c "whoami"
Invoke-AtomicTest T1070.001 -TestNumbers 1
```
5. Xác nhận cảnh báo được kích hoạt đúng.
![1](../screenshots/Wazuh_security_alerts_1.jpg)
![2](../screenshots/Wazuh_security_alerts_2.jpg)
![3](../screenshots/Wazuh_security_alerts_3.jpg)
![4](../screenshots/Wazuh_security_alerts_4.jpg)
![5](../screenshots/Wazuh_security_alerts_5.jpg)
![6](../screenshots/Wazuh_security_alerts_6.jpg)

## Kết quả đạt được

- Thiết lập hệ thống SIEM/EDR thu thập Telemetry từ 3 nguồn log chính: Sysmon, Windows Security, Windows System. Giám sát 12 Event ID quan trọng trên Endpoint Windows.
- Xây dựng 36 Detection Rules tùy chỉnh trong `local_rules.xml` gồm Rule ID `100001`–`100122` bao phủ 13 kỹ thuật MITRE ATT&CK trên 8 Tactics gồm: Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Command & Control.
- Áp dụng 3 cơ chế phát hiện: single-event matching, threshold-based detection (brute force: 5 lần/60 giây, recon: 5 lệnh/60 giây), và process-chain correlation (parent → child process, rule inheritance `if_sid`).
-  Triển khai pipeline dữ liệu khép kín: Endpoint → Sysmon → Wazuh Agent → Wazuh Manager → Dashboard với cơ chế cảnh báo tự động theo cấp độ nghiêm trọng (Level 5–15).
