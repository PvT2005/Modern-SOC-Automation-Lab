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
⚠️ Lưu ý quan trọng: Khi kết thúc, màn hình Terminal sẽ in ra thông tin đăng nhập (Username là admin và Password được sinh ngẫu nhiên).
 ## 3. Kiểm tra trạng thái dịch vụ
```bash
sudo systemctl status wazuh-manager
```
## 4. Truy cập giao diện quản trị
- Mở trình duyệt trên máy thật hoặc máy ảo có giao diện đồ họa.

- Truy cập vào địa chỉ IP của Ubuntu Server: https://192.168.56.10

- Đăng nhập với tài khoản admin và mật khẩu đã tạo.


## 5. Cấu hình Wazuh phục vụ tự động hóa

Dựa trên cấu trúc kiến trúc SOC, để phục vụ cho các Playbooks tự động hóa (SOAR/Shuffle) và nạp dữ liệu telemetry dạng thô đầy đủ nhất, chúng ta cần cấu hình Wazuh lưu Archive log vào định dạng JSON.

### Kích hoạt Logall JSON trong `ossec.conf`
Tính năng lưu trữ toàn bộ event thô bị tắt mặc định để tối ưu dung lượng. Để hệ thống có đủ log phân tích ta cấu hình file [/var/ossec/etc/ossec.conf](../Phase-2-Detection/wazuh_manager_ossec.conf)

Sửa hai giá trị `<logall>` và `<logall_json>` từ `no` thành `yes`:
```xml
  <global>
    <jsonout_output>yes</jsonout_output>
    <alerts_log>yes</alerts_log>
    <logall>yes</logall>
    <logall_json>yes</logall_json>
    ...
```


### Cấu hình Filebeat đọc file `archives.json`
Wazuh chỉ tạo file `/var/ossec/logs/archives/archives.json` nhưng chúng ta cần Filebeat đọc và gửi nó đến bộ cài Indexer. 

Cấu hình file [/etc/filebeat/filebeat.yml](../Phase-2-Detection/wazuh_manager_filebeat.yml)


### Khởi động lại dịch vụ
Hệ thống cần được khởi động lại để áp dụng module và config vừa nạp:

```bash
sudo systemctl restart wazuh-manager
sudo systemctl restart filebeat
```

