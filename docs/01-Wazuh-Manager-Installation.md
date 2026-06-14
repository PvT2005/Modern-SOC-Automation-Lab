# Cài đặt Wazuh Manager trên Ubuntu Server

Quá trình này sẽ thiết lập phần chính của hệ thống SOC - nơi tiếp nhận, phân tích và hiển thị toàn bộ Telemetry từ các Endpoint. 


## 1. Cài đặt Wazuh 
 ```bash 
curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh
sudo bash ./wazuh-install.sh -a
```
## 2. Truy cập giao diện quản trị
- Truy cập vào địa chỉ IP của Ubuntu Server: https://192.168.56.10
- Đăng nhập với tài khoản admin và mật khẩu đã tạo.
![wazuh-login](../screenshots/Wazuh-login.jpg)
- Giao diện dashboard
![wazuh-dashboard](../screenshots/Wazuh-Dashboard.jpg)




