# Deployment Guide - US Customs Knowledge Base

This guide covers multiple deployment scenarios for the customs knowledge base.

## Quick Summary

Choose your deployment method:

1. **Docker (Easiest)** - Complete stack with one command
2. **Cloud Platforms** - AWS, DigitalOcean, Railway, etc.
3. **Standalone Server** - Manual installation on Linux
4. **Embed in Code** - Use as library in your application
5. **Database Copy** - Transfer existing data to new server

---

## 1. Docker Deployment (Recommended)

**Prerequisites:** Docker and Docker Compose installed

```bash
# On your target server
git clone https://github.com/YOUR_USERNAME/customs-kb.git
cd customs-kb

# Configure environment
cp .env.example .env
nano .env  # Edit database passwords

# Build and start
docker-compose -f docker-compose.production.yml up -d --build

# Check health
curl http://localhost:8000/health
```

**Access:**
- API: http://your-server:8000
- Dashboard: http://your-server:8000/dashboard
- API Docs: http://your-server:8000/docs

**Important:** This deploys the application but NOT the data. See [Data Migration](#data-migration) below.

---

## 2. Cloud Platform Deployment

### AWS (ECS + RDS)

```bash
# 1. Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker build -f Dockerfile.production -t customs-kb .
docker push YOUR_ECR_URL/customs-kb:latest

# 2. Create RDS PostgreSQL (db.t3.micro or larger)
# 3. Deploy Qdrant on EC2 
# 4. Create ECS task definition pointing to RDS and Qdrant
# 5. Create ECS service with ALB
```

### DigitalOcean (Droplet + Managed DB)

```bash
# 1. Create 4GB+ Droplet
# 2. Add managed PostgreSQL database  
# 3. SSH and install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Deploy
git clone YOUR_REPO
cd customs-kb
docker-compose -f docker-compose.production.yml up -d
```

### Railway / Render (GitHub Integration)

1. Push code to GitHub
2. Connect repository in platform UI
3. Set environment variables
4. Deploy automatically

---

## 3. Standalone Server

Manual installation on Ubuntu/Debian:

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql-16 git

# Setup project
cd /opt
git clone YOUR_REPO customs-kb
cd customs-kb
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure PostgreSQL
sudo -u postgres psql
CREATE DATABASE customs_kb;
CREATE USER customs_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE customs_kb TO customs_user;
\q

# Initialize database
python scripts/init_db.py

# Create systemd service
sudo nano /etc/systemd/system/customs-kb.service
```

**Systemd service file:**
```ini
[Unit]
Description=US Customs KB API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/customs-kb
Environment="PATH=/opt/customs-kb/venv/bin"
ExecStart=/opt/customs-kb/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable customs-kb
sudo systemctl start customs-kb
```

---

## 4. Embed in Another Codebase

### As Microservice (Recommended)

Keep customs KB as separate API and call it:

```python
import httpx

CUSTOMS_KB_URL = "http://localhost:8000"

async def search_customs(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CUSTOMS_KB_URL}/api/search",
            params={"q": query, "limit": 5}
        )
        return response.json()
```

### As Python Library

```python
# Copy src/ directory into your project as customs_kb/
from customs_kb.query.semantic_search import SemanticSearch
from customs_kb.query.structured_query import StructuredQuery

semantic = SemanticSearch()
results = semantic.search("steel duties", limit=5)
```

### Shared Database

```python
# Multiple apps can query the same database
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@server/customs_kb")
# Query directly with SQL
```

---

## 5. Data Migration

**Export from local machine:**

```bash
# Export PostgreSQL
pg_dump -h localhost -U customs_user -d customs_kb -F c -f customs_kb.dump

# Export Qdrant (stop container first)
docker-compose stop qdrant
tar -czf qdrant_data.tar.gz ./qdrant_data/

# Transfer to remote server
scp customs_kb.dump user@server:/tmp/
scp qdrant_data.tar.gz user@server:/tmp/
```

**Import on remote server:**

```bash
# Import PostgreSQL
pg_restore -h localhost -U customs_user -d customs_kb /tmp/customs_kb.dump

# Import Qdrant
cd /opt/customs-kb
tar -xzf /tmp/qdrant_data.tar.gz
# Mount in docker-compose: ./qdrant_data:/qdrant/storage
```

**Complete backup script:**

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

pg_dump -h localhost -U customs_user -d customs_kb -F c -f $BACKUP_DIR/postgres.dump
docker-compose cp qdrant:/qdrant/storage $BACKUP_DIR/qdrant
cp .env $BACKUP_DIR/.env

tar -czf customs_kb_backup_$(date +%Y%m%d).tar.gz $BACKUP_DIR
echo "Backup complete"
```

---

## Environment Variables

```bash
# Required
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432
POSTGRES_DB=customs_kb
POSTGRES_USER=customs_user
POSTGRES_PASSWORD=your-secure-password

QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
QDRANT_COLLECTION=cbp_documents

# Optional
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

---

## HTTPS Setup (Nginx)

```nginx
server {
    listen 80;
    server_name customs-kb.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name customs-kb.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Security Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS with SSL certificate
- [ ] Set up firewall (ufw/iptables)
- [ ] Enable PostgreSQL SSL
- [ ] Add API authentication (JWT)
- [ ] Configure CORS for production domains
- [ ] Never commit secrets to git
- [ ] Set up automated backups
- [ ] Enable logging and monitoring

---

## Troubleshooting

**Can't connect to database:**
- Check firewall rules
- Verify credentials in .env
- Check pg_hba.conf for remote connections

**Qdrant not responding:**
- Verify container/service is running
- Check port 6333 is open
- Review Qdrant logs

**API returns 502:**
- Check all services are running
- Verify environment variables
- Check application logs

---

## Next Steps

1. Set up reverse proxy (nginx) with HTTPS
2. Configure automated backups
3. Add monitoring (Prometheus/Grafana)
4. Set up CI/CD (GitHub Actions)
5. Scale horizontally (load balancer + multiple instances)

See [README.md](README.md) and [CLAUDE.md](CLAUDE.md) for more information.
