# 🤖 Hướng dẫn Triển khai SOAR: Tines & Slack Integration
Tài liệu này trình bày cách xây dựng một luồng tự động hóa (SOAR Playbook) trên nền tảng Tines. Mục tiêu của Playbook là nhận cảnh báo từ LimaCharlie, trích xuất thông tin, gửi tin nhắn báo động qua Slack, và tạo một trang tương tác (Prompt) để chuyên viên SOC có thể bấm nút "Cô lập máy trạm" (Host Isolation) ngay lập tức chỉ với 1 click.

## 1. Khởi tạo Tines và Tạo Webhook
Đầu tiên, chúng ta cần tạo một "cái phễu" (Webhook) trên Tines để hứng dữ liệu do LimaCharlie bắn sang.

- Đăng ký Tines: Truy cập tines.com, đăng ký tài khoản Community Edition (Miễn phí).

- Tạo Story mới: Trong giao diện Tines, tạo một Story (Playbook) mới, đặt tên là LimaCharlie - Host Isolation Workflow.

- Tạo Webhook: * Kéo thả một Action loại Webhook từ menu bên trái vào màn hình (Canvas).

  - Đặt tên cho Action này là Catch LimaCharlie Alert.

  - Click vào Action, copy đường dẫn Webhook URL.

## 2. Nối LimaCharlie vào Tines
Bây giờ, mang cái URL vừa copy về lại LimaCharlie để "thông ống" dữ liệu.

- Đăng nhập LimaCharlie, vào mục Outputs.

- Nhấn + Add Output.

- Chọn:

  - Stream: Detections (Chỉ gửi những cảnh báo từ luật D&R).

  - Destination: Webhook.

- Điền tên (VD: Send_To_Tines) và dán Webhook URL của Tines vào ô Destination URL. Nhấn Save.

- Kích hoạt thử: Chạy lại file lazagne.exe trên Windows 10. Quay lại Tines, click vào Webhook Action, bạn sẽ thấy dữ liệu JSON của cảnh báo đã đổ về thành công!

## 3. Cấu hình Slack và Trích xuất Dữ liệu 
Để tin nhắn gửi đi thân thiện với người đọc, chúng ta cần lọc lấy các thông tin quan trọng (Tên máy, ID máy, File mã độc) và gửi sang Slack.

### 3.1. Trích xuất Dữ liệu 
- Kéo Action Event Transform vào Tines, nối nó với Webhook ở trên.

- Đặt tên là Extract Alert Data.

- Sử dụng cú pháp của Tines để lấy dữ liệu. Ví dụ:

  - hostname: <<Catch_LimaCharlie_Alert.body.routing.hostname>>

  - sensor_id: <<Catch_LimaCharlie_Alert.body.routing.sid>>

  - file_path: <<Catch_LimaCharlie_Alert.body.detect.event.FILE_PATH>>

### 3.2. Cấu hình Slack Message
- Tạo một Workspace Slack miễn phí. Tạo một kênh (Channel) tên là #soc-alerts.

- Trong Tines, chuyển sang tab Credentials, kết nối tài khoản Slack của bạn.

- Kéo Action Slack vào màn hình, nối với Action Extract Alert Data.

- Cấu hình nội dung tin nhắn cảnh báo chứa các biến vừa tạo:

```bash
🚨 *PHÁT HIỆN HÀNH VI LẤY CẮP MẬT KHẨU* 🚨
- Máy tính: <<Extract_Alert_Data.hostname>>
- Sensor ID: <<Extract_Alert_Data.sensor_id>>
- Tiến trình độc hại: <<Extract_Alert_Data.file_path>>
Vui lòng nhấp vào liên kết bên dưới để đưa ra quyết định xử lý.
```
## 4. Xây dựng Trang Tương tác "User Prompt"
Đây là điểm nhấn "ăn tiền" nhất của hệ thống SOAR. Thay vì phải vào tận LimaCharlie để gõ lệnh, Tines cho phép tạo một trang web (Tines Page) nhỏ để bạn bấm nút.

- Kéo Action Page vào màn hình. Đặt tên là Isolation Prompt.

- Cấu hình trang này có 2 nút bấm (Boolean/Choice):

  - Yes, Isolate this Machine! (Có, cô lập máy này)

  - No, Ignore it! (Không, bỏ qua)

- Quay lại Action Slack ở phần 3, thêm đường link của cái Page này vào cuối tin nhắn Slack: Link xử lý: <<Isolation_Prompt.url>>

## 5. Thực thi Cô lập Máy trạm qua API
Nếu người dùng chọn "Yes" trên Tines Page, Tines sẽ tự động gọi API của LimaCharlie để ra lệnh cắt mạng máy Windows.

### 5.1. Lấy API Key (JWT) từ LimaCharlie
- Quay lại LimaCharlie -> REST API.

- Copy mã JWT (JSON Web Token) cấp quyền tương tác với Sensor. Tạo một Credential tên là LimaCharlie_API trên Tines để lưu mã này.

### 5.2. Cấu hình Action HTTP Request
- Nối một Action Trigger sau cái Isolation Prompt để lọc: Chỉ đi tiếp nếu người dùng chọn Yes.

- Kéo Action HTTP Request vào cuối luồng, đặt tên là Isolate Sensor.

- Cấu hình gọi API LimaCharlie:

  - URL: https://api.limacharlie.io/v1/sensor/<<Extract_Alert_Data.sensor_id>>/isolation

  - Method: POST

  - Headers: Authorization: Bearer <<LimaCharlie_API>>

  - Payload/Body: {"is_isolated": true}

🎯 Kiểm thử Toàn hệ thống (End-to-End Test)
Đây là lúc bạn chiêm ngưỡng thành quả của Phase 3:

Mở máy ảo Windows 10, mở sẵn một cửa sổ Ping Google (ping 8.8.8.8 -t).

Chạy file lazagne.exe.

Luồng tự động: Trong vòng 3 giây, điện thoại/máy tính của bạn sẽ nổ thông báo Slack.

Bấm vào link trên Slack, chọn Yes, Isolate.

Nhìn lại màn hình Windows 10: Lệnh Ping lập tức báo Request timed out. Kẻ tấn công đã bị nhốt hoàn toàn!

💡 Lưu ý Khôi phục: Để mở lại mạng cho máy Windows 10, bạn có thể vào trực tiếp Dashboard của LimaCharlie, tìm đến Sensor đó và nhấn nút Remove Isolation.