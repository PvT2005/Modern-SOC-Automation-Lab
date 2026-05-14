# 🔍 Phase 1: Lắng nghe, Giám sát và Phát hiện Mối đe dọa

Thiết lập nền tảng giám sát toàn diện — từ thu thập Telemetry chuyên sâu trên Endpoint đến phân tích, phát hiện và quản lý cảnh báo theo khung MITRE ATT&CK.

Giai đoạn này triển khai kiến trúc SIEM kết hợp với nền tảng quản lý sự cố. Tại đây, mọi sự kiện, luồng mạng và hành vi trên máy trạm sẽ được tổng hợp, phân tích dựa trên các luật cảnh báo để chỉ mặt đặt tên các rủi ro bảo mật trước khi chúng gây hại lớn hơn.

---

## 🧩 Công cụ sử dụng

- **Wazuh (SIEM/XDR)**: Đóng vai trò là trung tâm "Thu thập và Phân tích". Thu nhận log, chạy đối chiếu với thư viện luật và đánh giá các hành vi bất thường.

- **Sysmon** *(với cấu hình SwiftOnSecurity)*: Đóng vai trò giám sát sâu trên Windows. Theo dõi mọi hành động khởi tạo tiến trình, chỉnh sửa Registry hay kết nối mạng và báo cáo lại với độ chi tiết vượt trội so với Windows Event Log mặc định.

- **Atomic Red Team**: Bộ công cụ kiểm thử mã nguồn mở ánh xạ trực tiếp với khung MITRE ATT&CK. Dùng để giả lập các kỹ thuật tấn công thực tế (ví dụ: T1003 - OS Credential Dumping, T1059 - Command & Scripting) trên máy trạm Windows mục tiêu nhằm xác thực khả năng phát hiện của hệ thống.

- **TheHive**: Đóng vai trò "Bàn làm việc của chuyên viên SOC". Nền tảng tiếp nhận tín hiệu từ Wazuh, giúp chuyên gia bảo mật điều phối, gắn nhãn Cases và theo dõi tiến trình xử lý sự cố.

- **Elasticsearch & Cassandra**: Các "Kho lưu trữ" cơ sở dữ liệu, phụ trách lưu vết và tra cứu chỉ mục phục vụ truy xuất tốc độ cao cho hệ thống TheHive.

---

## 🔄 Luồng Phát hiện (Detection Workflow)

Hệ thống vận hành theo chu trình khép kín sau:

- **Telemetry Collection**: Sysmon và Windows Event Logs túc trực trên Windows Endpoint ghi nhận từng hành vi nhỏ nhất. Trình Wazuh Agent liên tục đóng gói các sự kiện này và đẩy về máy chủ Wazuh trung tâm.

- **Attack Simulation**: Atomic Red Team thực thi các kịch bản tấn công được lập trình sẵn theo từng Technique ID của MITRE ATT&CK. Đây là bước tạo ra "chất liệu thô" để xây dựng và kiểm thử Detection Rules.

- **Analysis & Detection**: Wazuh Manager tiếp nhận và bắt đầu bóc tách, chuẩn hóa dữ liệu log. Hệ thống đối chiếu với bộ luật tùy chỉnh (`local_rules.xml`). Nếu một tiến trình thỏa mãn điều kiện nghi ngờ, hệ thống lập tức kích hoạt cảnh báo.

- **Alerting & Routing**: Một Webhook được Wazuh Manager tự động đẩy sang API của nền tảng TheHive, chuyển kèm chi tiết đầy đủ về loại cảnh báo, thời gian và thông tin máy chủ bị ảnh hưởng.

- **Case Management**: Tại TheHive, cảnh báo được tạo tự động để đội ngũ SOC tiếp nhận. Từ Alert này, chuyên viên có thể nhóm các cảnh báo liên quan lại và nâng cấp thành một Case phục vụ điều tra mở rộng chuyên sâu.

---

## ⚔️ Attack Simulation & Detection Engineering

Đây là phần cốt lõi chứng minh giá trị của toàn bộ hệ thống — biến Lab từ môi trường "chạy được" thành môi trường "phát hiện được".

### Quy trình thực hiện

1. **Giả lập tấn công** bằng Atomic Red Team trên máy Windows mục tiêu.
2. **Quan sát log thô** đổ về Wazuh Dashboard — xác định `event_id`, `process_name`, `command_line` đặc trưng.
3. **Viết Detection Rule** tùy chỉnh vào `local_rules.xml` dựa trên dấu hiệu đã phân tích.
4. **Kiểm thử lại** bằng cách tái giả lập tấn công và xác nhận cảnh báo được kích hoạt đúng.

### Các kỹ thuật đã mô phỏng

| MITRE ID | Tên kỹ thuật | Công cụ giả lập | Trạng thái |
|---|---|---|---|
| T1003 | OS Credential Dumping | Atomic Red Team | ✅ Có Detection Rule |
| T1059.001 | PowerShell Execution | Atomic Red Team | ✅ Có Detection Rule |
| T1547 | Registry Run Keys / Startup Folder | Atomic Red Team | ✅ Có Detection Rule |
| T1055 | Process Injection | Atomic Red Team | 🔄 Đang phát triển |

---

## 📂 Giải thích các File Cấu hình

- [sysmonconfig.xml](./sysmonconfig.xml): Bộ luật chuẩn của Sysmon (SwiftOnSecurity) cài trên máy trạm Windows, được tối ưu để giảm tải các sự kiện rác đồng thời tập trung bắt sóng chính xác các kỹ thuật tấn công phổ biến.

- [wazuh_agent_ossec.conf](./wazuh_agent_ossec.conf): File cấu hình trên Windows cài Wazuh Agent để khai báo địa chỉ IP của Wazuh Manager và quy định các dạng event log sẽ thu thập (bao gồm kênh Sysmon Operational).

- [wazuh_manager_filebeat.yml](./wazuh_manager_filebeat.yml) / [wazuh_manager_ossec.conf](./wazuh_manager_ossec.conf): Cấu hình trên máy chủ SIEM (Wazuh Manager) phụ trách định tuyến, tích hợp chia sẻ log và kích hoạt lưu trữ archive JSON phục vụ phân tích.

- [docker-compose.yml](./docker-compose.yml): Kịch bản tự động hóa triển khai bằng Docker. Cho phép kéo image, gắn volume, mở cấu hình mạng và dựng toàn bộ nền tảng TheHive kèm Datastore chỉ bằng một lệnh duy nhất.

- [application.conf](./application.conf): Cấu hình chính của TheHive, định nghĩa khóa bí mật, kết nối đến Elasticsearch, Cassandra và chuẩn bị cổng giao tiếp.

- [cassandra.yaml](./cassandra.yaml) / [elasticsearch.yml](./elasticsearch.yml) / [jvm.options](./jvm.options): Các tinh chỉnh kỹ thuật, phân bổ tối ưu hóa bộ nhớ cho dịch vụ và cấu hình các cụm dữ liệu phân tán hỗ trợ background cho TheHive.

---

## 📚 Deployment Guides

- [00-Ubuntu-Server-Setup.md](../docs/00-Ubuntu-Server-Setup.md): Các bước chuẩn bị, cài đặt môi trường cơ bản trên máy chủ Ubuntu trước khi triển khai hệ thống lõi.
- [01-Wazuh-Manager-Installation.md](../docs/01-Wazuh-Manager-Installation.md): Hướng dẫn cài đặt, thiết lập và cấu hình trung tâm SIEM Wazuh.
- [02-TheHive-Docker-Deployment.md](../docs/02-TheHive-Docker-Deployment.md): Hướng dẫn khởi chạy nền tảng TheHive siêu tốc thông qua Docker để vận hành quy trình quản lý sự cố.
- [03-Windows-Endpoint-Setup.md](../docs/03-Windows-Endpoint-Setup.md): Các bước cài đặt máy tính mục tiêu, tích hợp giám sát Sysmon và kết nối Wazuh Agent vào mạng lưới truyền log trung tâm.

---

## 🎯 Kết quả đạt được

- ✅ Thiết lập hệ thống **SIEM/EDR** giám sát **50+ sự kiện hệ thống** trên nền tảng Wazuh + Sysmon.
- ✅ Xây dựng **10+ Detection Rules** tùy chỉnh (`local_rules.xml`) ánh xạ trực tiếp với các kỹ thuật trong khung **MITRE ATT&CK**.
- ✅ Triển khai pipeline dữ liệu khép kín: **Endpoint → Sysmon → Wazuh → TheHive** với cơ chế cảnh báo tự động.
- ✅ Vận hành thành công **Attack Simulation** bằng Atomic Red Team để kiểm thử và cải thiện khả năng phát hiện.
