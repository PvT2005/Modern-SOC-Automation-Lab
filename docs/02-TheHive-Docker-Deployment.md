# 🐝 Deploying TheHive using Docker Compose

TheHive là nền tảng Case Management dành riêng cho các đội phản ứng sự cố (CERT/SOC). Để quản lý dễ dàng và tách biệt môi trường, hệ thống này được triển khai dưới dạng Docker Containers.

## 1. Cài đặt Docker và Docker Compose
```bash
sudo apt install docker.io docker-compose -y
sudo systemctl enable --now docker
```
## 2. Cấu hình file docker-compose.yml
```bash
mkdir thehive && cd thehive
nano docker-compose.yml
```
Cấu hình file [docker-compose.yml](../Phase-2-Detection/docker-compose.yml)

## 3. Khởi chạy hệ thống
```bash
sudo docker-compose up -d
sudo docker ps
```
## 4. Truy cập hệ thống
Mở trình duyệt và truy cập: http://192.168.56.10:9000


## 5. Cấu hình hệ thống TheHive, Cassandra và Elasticsearch

Trong môi trường Docker, các cấu hình này được thực hiện thông qua việc mount các file `.yaml`/`.conf` vào bên trong container. 

### Cấu hình Cassandra
Tạo thư mục chứa cấu hình và tạo file [cassandra.yaml](../Phase-2-Detection/cassandra.yaml) để cấu hình Cluster và địa chỉ lắng nghe.

```bash
mkdir -p ./cassandra_config
nano ./cassandra_config/cassandra.yaml
```


### Cấu hình Elasticsearch và giới hạn RAM
Để TheHive có thể Index một cách ổn định, ta tạo cấu hình cho [elasticsearch.yml](../Phase-2-Detection/elasticsearch.yml) và thiết lập giới hạn RAM để tránh lỗi Crash hệ thống:
```bash
mkdir -p ./elasticsearch_config
nano ./elasticsearch_config/elasticsearch.yml
```

Tiếp theo, tạo file cấu hình [jvm.options](../Phase-2-Detection/jvm.options) cho Java Virtual Machine để giới hạn sử dụng 2GB RAM và fix lỗi `log4j2`:
```bash
nano ./elasticsearch_config/jvm.options
```


### Cấu hình TheHive
TheHive yêu cầu một Secret Key để bảo mật phiên đăng nhập và mã hóa.
Chạy lệnh sau trên Terminal để lấy ra một chuỗi ngẫu nhiên và sao chép lại:
```bash
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
```

Sau đó tạo thư mục và mở file cấu hình [application.conf](../Phase-2-Detection/application.conf) chính của TheHive:
```bash
mkdir -p ./thehive_config
nano ./thehive_config/application.conf
```


### Bước 5.4: Cập nhật lại `docker-compose.yml`
Khi các file cấu hình đã được tạo, bạn sửa lại file [docker-compose.yml](../Phase-2-Detection/docker-compose.yml) 

Cuối cùng, khởi động lại toàn bộ stack để nạp cấu hình mới:
```bash
sudo docker-compose down
sudo docker-compose up -d
```
