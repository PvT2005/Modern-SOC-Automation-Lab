
# 🤖 Phase 3: SOC Automation & Interactive Incident Response (SOAR)
Nếu Phase 2 tập trung vào việc "Lắng nghe và Giám sát" (Detection), thì Phase 3 đánh dấu bước ngoặt nâng cấp hệ thống lên cấp độ Chủ động Phản ứng (Active Response).

Giai đoạn này triển khai kiến trúc SOAR (Security Orchestration, Automation, and Response) kết hợp với EDR (Endpoint Detection and Response) để tạo ra một luồng xử lý sự cố tự động. Thay vì chuyên viên SOC phải thao tác thủ công, hệ thống sẽ tự động phát hiện, báo động qua kênh chat, và cho phép cô lập máy trạm bị nhiễm mã độc chỉ với một cú click chuột.

## 🧩 Công cụ sử dụng
- LimaCharlie (EDR): Đóng vai trò là "Đặc nhiệm" trên Endpoint. Phát hiện mã độc (LaZagne) và thực thi lệnh cắt mạng (Host Isolation).

- Tines (SOAR): Đóng vai trò "Bộ não điều phối". Nhận Webhook, xử lý logic, tạo trang tương tác (User Prompt) và gọi API ngược lại EDR.

- Slack: Kênh giao tiếp và cảnh báo thời gian thực (Real-time Alerting).

## 🔄 Luồng Tự động hóa (Automation Workflow)
Hệ thống vận hành theo chu trình khép kín sau:

- Detection: LimaCharlie Sensor trên Windows 10 phát hiện tiến trình độc hại lazagne.exe được thực thi dựa trên bộ luật D&R tùy chỉnh.

- Trigger: LimaCharlie tự động đóng gói dữ liệu cảnh báo thành định dạng JSON và đẩy qua Webhook của Tines.

- Data Extraction: Tines phân tích cú pháp JSON, trích xuất các trường thông tin quan trọng như: Hostname, Sensor ID, và File Path.

- Interactive Prompt: Tines gửi một cảnh báo đến kênh #soc-alerts trên Slack kèm theo một đường link bảo mật. Đường link này dẫn đến một trang web nội bộ (Tines Page) chứa 2 nút quyết định: "Yes, Isolate" hoặc "No, Ignore".

- Execution: Nếu chuyên viên SOC bấm nút "Isolate", Tines lập tức gọi REST API của LimaCharlie kèm theo JWT Token, ra lệnh cô lập máy trạm Windows khỏi toàn bộ mạng nội bộ ngay tắp lự.

## 📂 Giải thích các File Cấu hình

- [limacharlie_dr_rules.yaml](./limacharlie_dr_rules.yaml): Chứa bộ quy tắc Phát hiện & Phản hồi (Detection & Response Rules). Luật này quy định chính xác điều kiện nào thì LimaCharlie được phép kích hoạt báo động gửi cho Tines.

- [tines_host_isolation_story.json](./tines_host_isolation_story.json): Bản xuất (Export) toàn bộ kịch bản tự động hóa trên Tines. Bạn có thể Import file này vào môi trường Tines của mình để xem trực quan các Node logic (Webhook, Event Transform, HTTP Request).

## 📚 Deployment Guides
[04-LimaCharlie-Deployment-Guide.md](../docs/04-LimaCharlie-Deployment-Guide.md): Cách triển khai EDR Sensor và thiết lập D&R Rule.
[05-Tines-and-Slack-Setup.md](../docs/05-Tines-and-Slack-Setup.md): Cách nối Webhook, xây dựng luồng SOAR, tạo Tines Page và kết nối Slack API.

🎯 Kết quả đạt được: Giảm thời gian phản ứng sự cố (MTTR - Mean Time To Respond) từ mức "hàng chục phút" xuống chỉ còn "vài giây", hạn chế tối đa rủi ro mã độc lây lan ngang (Lateral Movement) trong mạng nội bộ.