# 🖥️ Thiết lập Hạ tầng: Ubuntu Server (SOC Brain)
Đây là bước chuẩn bị nền tảng hệ điều hành, Ubuntu Server được tinh chỉnh để chạy hoàn toàn qua dòng lệnh và cài đặt Wazuh Manager và TheHive .

## 1. Cấu hình Máy ảo 
- OS: Ubuntu Server 22.04 LTS .

- CPU: 4 Cores.

- RAM: 16GB

## 2. Cấu hình Mạng nội bộ 
- Network Adapter: Chế độ Host-Only 
- Địa chỉ IP : 192.168.56.10
- Địa chỉ IP Win10: 192.168.56.20
- Subnet: 255.255.255.0 (/24)


## 3. Cập nhật hệ thống & Công cụ cơ bản
Truy cập vào máy chủ Ubuntu và chuẩn bị các công cụ quản trị cần thiết:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install openssh-server curl nano -y
```

## 4. Cài đặt Ngrok
Vì sử dụng Shuffle trên Cloud thay vì cài Local để tiết kiệm RAM, Ngrok là thành phần bắt buộc. Nó tạo ra các "đường hầm" an toàn để Shuffle Cloud có thể gửi lệnh điều khiển ngược về TheHive và Wazuh đang nằm ở IP nội bộ 192.168.56.10.

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok -y

# Xác thực tài khoản Ngrok (Lấy Auth Token từ ngrok.com)
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```
- 💡 Cách sử dụng trong Lab: > Khi cần Shuffle kết nối với TheHive, chạy lệnh: ngrok http 9000
- Khi cần Shuffle kết nối với Wazuh API, chạy lệnh: ngrok http 55000
