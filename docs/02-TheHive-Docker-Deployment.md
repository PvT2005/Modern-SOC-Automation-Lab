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
Cấu hình file docker-compose.yml
```bash
version: "3"
services:
  elasticsearch:
    image: elasticsearch:7.17.9
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - ./elasticsearch_data:/usr/share/elasticsearch/data
  
  cassandra:
    image: cassandra:4
    volumes:
      - ./cassandra_data:/var/lib/cassandra

  thehive:
    image: thehiveproject/thehive4:latest
    depends_on:
      - elasticsearch
      - cassandra
    ports:
      - "9000:9000"
    environment:
      - TH_ELASTICSEARCH_URI=http://elasticsearch:9200
      - TH_CASSANDRA_HOSTS=cassandra
```
## 3. Khởi chạy hệ thống
```bash
sudo docker-compose up -d
sudo docker ps
```
## 4. Truy cập hệ thống
Mở trình duyệt và truy cập: http://192.168.56.10:9000
