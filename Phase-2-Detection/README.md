# 🔍 Phase 2: Lắng nghe, Giám sát và Quản lý Cảnh báo 

Nếu Phase 1 tập trung vào việc chuẩn bị môi trường và tạo ra các kịch bản tấn công giả lập, thì Phase 2 đánh dấu bước thiết lập "tai mắt" cho hệ thống, nâng cấp khả năng thu thập dữ liệu và chủ động phát hiện sớm mối đe dọa.

Giai đoạn này triển khai kiến trúc SIEM kết hợp với nền tảng quản lý sự cố. Tại đây, mọi sự kiện, luồng mạng và hành vi trên máy trạm sẽ được tổng hợp, phân tích dựa trên các luật cảnh báo để chỉ mặt đặt tên các rủi ro bảo mật trước khi chúng gây hại lớn hơn.

## 🧩 Công cụ sử dụng
- **Wazuh (SIEM/XDR)**: Đóng vai trò là trung tâm "Thu thập và Phân tích". Thu nhận log, chạy đối chiếu với thư viện luật và đánh giá các hành vi bất thường.

- **Sysmon**: Đóng vai trò giám sát sâu trên Windows. Nó theo dõi mọi hành động khởi tạo tiến trình, chỉnh sửa Registry hay kết nối mạng và báo cáo lại.

- **TheHive**: Đóng vai trò "Bàn làm việc của chuyên viên SOC". Một nền tảng tiếp nhận tín hiệu từ Wazuh, giúp chuyên gia bảo mật điều phối, gắn nhãn Cases và theo dõi tiến trình xử lý sự cố.

- **Elasticsearch & Cassandra**: Các "Kho lưu trữ" cơ sở dữ liệu, phụ trách lưu vết và tra cứu chỉ mục phục vụ truy xuất tốc độ cao cho hệ thống TheHive.

## 🔄 Luồng Phát hiện (Detection Workflow)
Hệ thống vận hành theo chu trình khép kín sau:

- **Telemetry Collection**: Sysmon và Windows Event Logs túc trực trên Windows Endpoint ghi nhận từng hành vi nhỏ nhất. Trình Wazuh Agent liên tục đóng gói các sự kiện này và đẩy về máy chủ Wazuh trung tâm.

- **Analysis & Detection**: Wazuh Manager tiếp nhận và bắt đầu bóc tách, chuẩn hóa dữ liệu log. Nếu một tiến trình thỏa mãn điều kiện nghi ngờ, hệ thống lập tức kích hoạt cảnh báo.

- **Alerting & Routing**: Một Webhook được Wazuh Manager tự động đẩy sang API của nền tảng TheHive, chuyển kèm chi tiết đầy đủ về loại cảnh báo, thời gian và thông tin máy chủ bị ảnh hưởng.

- **Case Management**: Tại TheHive, cảnh báo được tạo tự động để đội ngũ SOC tiếp nhận. Từ Alert này, chuyên viên có thể nhóm các cảnh báo liên quan lại và nâng cấp thành một Case phục vụ điều tra mở rộng chuyên sâu.

## 📂 Giải thích các File Cấu hình

- [application.conf](./application.conf): Cấu hình chính của TheHive, định nghĩa khóa bí mật, kết nối đến Elasticsearch, Cassandra và chuẩn bị cổng giao tiếp.

- [cassandra.yaml](./cassandra.yaml) / [elasticsearch.yml](./elasticsearch.yml) / [jvm.options](./jvm.options): Các tinh chỉnh kỹ thuật, phân bổ tối ưu hóa bộ nhớ cho dịch vụ và cấu hình các cụm dữ liệu phân tán hỗ trợ background cho TheHive.

- [docker-compose.yml](./docker-compose.yml): Kịch bản tự động hóa triển khai bằng Docker. Cho phép kéo image, gắn volume, mở cấu hình mạng và dựng toàn bộ nền tảng TheHive kèm Datastore chỉ bằng một lệnh duy nhất.

- [sysmonconfig.xml](./sysmonconfig.xml): Bộ luật chuẩn của Sysmon cài trên máy trạm Windows, nó được tối ưu để giảm tải các sự kiện rác đồng thời tập trung bắt sóng chính xác các kỹ thuật tấn công phổ biến.

- [wazuh_agent_ossec.conf](./wazuh_agent_ossec.conf): File cấu hình trên Windows cài Wazuh Agent để khai báo địa chỉ IP của Wazuh Manager và quy định các dạng event log sẽ thu thập.

- [wazuh_manager_filebeat.yml](./wazuh_manager_filebeat.yml) / [wazuh_manager_ossec.conf](./wazuh_manager_ossec.conf): Cấu hình cài đặt trên máy chủ SIEM (Wazuh Manager) phụ trách việc định tuyến, tích hợp chia sẻ log và điều chỉnh cài đặt hệ thống trung tâm.

## 📚 Deployment Guides
- [00-Ubuntu-Server-Setup.md](../docs/00-Ubuntu-Server-Setup.md): Các bước chuẩn bị, cài đặt môi trường cơ bản trên máy chủ Ubuntu trước khi triển khai hệ thống lõi.
- [01-Wazuh-Manager-Installation.md](../docs/01-Wazuh-Manager-Installation.md): Hướng dẫn cài đặt, thiết lập và cấu hình trung tâm SIEM Wazuh.
- [02-TheHive-Docker-Deployment.md](../docs/02-TheHive-Docker-Deployment.md): Hướng dẫn khởi chạy nền tảng TheHive siêu tốc thông qua Docker để vận hành quy trình quản lý sự cố.
- [03-Windows-Endpoint-Setup.md](../docs/03-Windows-Endpoint-Setup.md): Các bước cài đặt máy tính mục tiêu, tích hợp giám sát Sysmon và kết nối Wazuh Agent vào mạng lưới truyền log trung tâm.

🎯 **Kết quả đạt được:** Tổ chức thành công một hệ thống giám sát tập trung, có khả năng tự động nhận diện và cảnh báo sớm các hành vi độc hại từ Endpoint. Song song đó, thiết lập hoàn chỉnh không gian làm việc chuyên nghiệp (TheHive) tạo đà cho Phase tự động hóa phản hồi tiếp theo.
