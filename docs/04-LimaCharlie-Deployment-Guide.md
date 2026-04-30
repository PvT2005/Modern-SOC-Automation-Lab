# 🛡️ Hướng dẫn Cài đặt và Cấu hình LimaCharlie EDR
Tài liệu này hướng dẫn cách triển khai LimaCharlie - một nền tảng SecOps Cloud (EDR) lên máy trạm Windows 10.LimaCharlie sẽ đóng vai trò là "đặc nhiệm", không chỉ phát hiện mã độc mà còn nhận lệnh từ Tines (SOAR) để cô lập máy trạm khỏi mạng nội bộ khi có sự cố.

## 1. Khởi tạo Organization trên LimaCharlie 
Đầu tiên, chúng ta cần tạo một môi trường quản lý trên Cloud của LimaCharlie.

- Truy cập LimaCharlie.io và đăng ký một tài khoản miễn phí.

- Đăng nhập vào hệ thống và nhấn Create Organization.

- Điền thông tin:

  - Name: SOC-Lab-Trung (hoặc tên bất kỳ).

  - Data Residency: Chọn khu vực gần nhất hoặc mặc định (VD: US).

  - Template: Chọn Extended Detection & Response Standard.

- Nhấn Create để hoàn tất.

## 2. Lấy Installation Key và Tải Sensor
Để cài đặt EDR lên máy trạm, chúng ta cần một chìa khóa xác thực (Installation Key).

- Tại Dashboard của Organization vừa tạo, nhìn sang menu bên trái, chọn Sensors -> Installation Keys.

- Nhấn nút + Create Installation Key.

- Đặt tên cho Key (VD: Windows-10-Key) và nhấn Create. Copy lại chuỗi Key này.

- Chuyển sang tab Downloads (hoặc Sensor Downloads), tải xuống file cài đặt cho Windows 64-bit (File có dạng hcp_windows_amd64.exe).

## 3. Cài đặt LimaCharlie Sensor lên Windows 10
Bây giờ chúng ta sẽ đưa "đặc nhiệm" vào máy mục tiêu.

- Chép file hcp_windows_amd64.exe vừa tải vào máy ảo Windows 10.

- Mở Command Prompt (Run as Administrator).

- Di chuyển đến thư mục chứa file cài đặt và chạy lệnh sau (thay <YOUR_INSTALLATION_KEY> bằng key bạn đã copy ở bước 2):

```bash
hcp_windows_amd64.exe -i <YOUR_INSTALLATION_KEY>
```
✅ Kiểm tra kết quả: > * Quá trình cài đặt diễn ra ngầm (Silent Install). Sẽ không có cửa sổ nào hiện lên.

- Quay lại Dashboard của LimaCharlie trên trình duyệt, vào mục Sensors -> List. Bạn sẽ thấy máy Windows 10 của mình xuất hiện với trạng thái màu xanh (Online).

## 4. Kích hoạt Telemetry và Giả lập Tấn công
Để kiểm tra EDR có hoạt động không, chúng ta sẽ giả lập một hành vi đánh cắp mật khẩu bằng công cụ LaZagne (Giống hệt kịch bản của MyDFIR).

- Tắt tạm thời Windows Defender trên máy ảo Windows 10 (để nó không xóa file của chúng ta trước khi LimaCharlie kịp đọc).

- Tải công cụ LaZagne (file .exe) từ GitHub về máy Windows 10.

- Mở Command Prompt và chạy file lazagne.exe.

- Trên LimaCharlie Dashboard, chọn máy Windows 10 -> Chuyển sang tab Timeline. Bạn sẽ thấy log hệ thống đổ về liên tục, trong đó có sự kiện NEW_PROCESS liên quan đến lazagne.exe.

## 5. Viết luật Phát hiện & Phản hồi (D&R Rule)
Chúng ta phải dạy LimaCharlie cách nhận diện file lazagne.exe để sau này nó còn gửi cảnh báo (Alert) sang cho Tines.

- Trên menu trái của LimaCharlie, chọn Automation -> D&R Rules.

- Nhấn + New Rule.

- Màn hình sẽ chia làm 2 phần: Detect (Điều kiện phát hiện) và Respond (Hành động). Hãy điền các đoạn mã YAML sau:

Phần Detect:
```bash
events:
  - NEW_PROCESS
  - EXISTING_PROCESS
op: ends with
path: event/FILE_PATH
value: lazagne.exe
```

Phần Respond:

```bassh
- action: report
  name: SOC_Lab_Credential_Dumping_Detected
```
(Giải thích: Khi phát hiện, hãy tạo ra một Báo cáo/Cảnh báo có tên là "SOC_Lab_Credential_Dumping_Detected").

- Kéo xuống dưới, nhập tên cho Rule này (VD: Detect LaZagne) và nhấn Save.
- Hãy quay lại máy Windows 10 và chạy file lazagne.exe một lần nữa.Nếu bạn vào mục Detections trên LimaCharlie và thấy cảnh báo màu đỏ mang tên SOC_Lab_Credential_Dumping_Detected hiện lên