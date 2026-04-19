# 🛠️ Installing Wazuh Manager on Ubuntu Server

Quá trình này sẽ thiết lập "trái tim" của hệ thống SOC - nơi tiếp nhận, phân tích và hiển thị toàn bộ Telemetry từ các Endpoint. Việc cài đặt Native giúp tối ưu hóa tài nguyên phần cứng và quản lý sâu ở cấp độ hệ điều hành.

## 1. Cập nhật hệ thống

```bash
sudo apt update && sudo apt upgrade -y
```
## 2. Cài đặt Wazuh 
 ```bash 
curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh
sudo bash ./wazuh-install.sh -a
```
⚠️ Lưu ý quan trọng: Khi kết thúc, màn hình Terminal sẽ in ra thông tin đăng nhập (Username là admin và Password được sinh ngẫu nhiên). Hãy copy và lưu trữ mật khẩu này thật cẩn thận!
 ## 3. Kiểm tra trạng thái dịch vụ
```bash
sudo systemctl status wazuh-manager
```
## 4. Truy cập giao diện quản trị
- Mở trình duyệt trên máy thật hoặc máy ảo có giao diện đồ họa.

- Truy cập vào địa chỉ IP của Ubuntu Server: https://192.168.56.10

- Đăng nhập với tài khoản admin và mật khẩu đã tạo.