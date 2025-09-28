# BTC Trading Bot - Production Deployment

This guide covers deploying the BTC Trading Bot to production environments.

## 🎯 Deployment Options

### 1. Docker Compose (Recommended)
### 2. Docker Swarm
### 3. Kubernetes
### 4. Cloud Platforms (AWS, GCP, Azure)
### 5. VPS/Dedicated Server

---

## 🐳 Docker Compose Deployment

### Production Setup

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker $USER

   # Install Docker Compose
   sudo apt install docker-compose -y

   # Create app directory
   sudo mkdir -p /opt/btc-trading-bot
   sudo chown $USER:$USER /opt/btc-trading-bot
   cd /opt/btc-trading-bot
   ```

2. **Deploy Application**
   ```bash
   # Clone repository
   git clone <repository-url> .

   # Setup production environment
   cp .env.example .env
   # Edit .env with production values

   # Setup credentials
   # Upload service_account.json
   # Upload token.json (if using OAuth)

   # Create production docker-compose
   cp docker-compose.yml docker-compose.prod.yml
   # Edit for production settings
   ```

3. **Production docker-compose.prod.yml**
   ```yaml
   version: '3.8'

   services:
     btc-trading-bot:
       build: .
       container_name: btc-trading-bot-prod
       restart: unless-stopped
       ports:
         - "80:8000"  # or use reverse proxy
       environment:
         - DEBUG=false
         - LOG_LEVEL=INFO
       env_file:
         - .env
       volumes:
         - ./data:/app/data
         - ./service_account.json:/app/service_account.json:ro
         - /etc/localtime:/etc/localtime:ro
       logging:
         driver: "json-file"
         options:
           max-size: "100m"
           max-file: "10"
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 30s

     # Optional: Reverse proxy
     nginx:
       image: nginx:alpine
       container_name: btc-bot-nginx
       restart: unless-stopped
       ports:
         - "443:443"
         - "80:80"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - btc-trading-bot
   ```

4. **Start Production**
   ```bash
   # Start services
   docker-compose -f docker-compose.prod.yml up -d

   # Verify deployment
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs -f
   ```

---

## ☁️ Cloud Deployment

### AWS ECS Deployment

1. **Create ECS Task Definition**
   ```json
   {
     "family": "btc-trading-bot",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
     "taskRoleArn": "arn:aws:iam::ACCOUNT:role/btc-bot-task-role",
     "containerDefinitions": [{
       "name": "btc-trading-bot",
       "image": "your-account.dkr.ecr.region.amazonaws.com/btc-trading-bot:latest",
       "portMappings": [{
         "containerPort": 8000,
         "protocol": "tcp"
       }],
       "environment": [
         {"name": "DEBUG", "value": "false"},
         {"name": "HOST", "value": "0.0.0.0"},
         {"name": "PORT", "value": "8000"}
       ],
       "secrets": [
         {"name": "GOOGLE_SHEET_ID", "valueFrom": "arn:aws:secretsmanager:region:account:secret:btc-bot/google-sheet-id"},
         {"name": "TELEGRAM_BOT_TOKEN", "valueFrom": "arn:aws:secretsmanager:region:account:secret:btc-bot/telegram-token"}
       ],
       "logConfiguration": {
         "logDriver": "awslogs",
         "options": {
           "awslogs-group": "/ecs/btc-trading-bot",
           "awslogs-region": "us-east-1",
           "awslogs-stream-prefix": "ecs"
         }
       },
       "healthCheck": {
         "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
         "interval": 30,
         "timeout": 5,
         "retries": 3,
         "startPeriod": 30
       }
     }]
   }
   ```

2. **Deploy to ECS**
   ```bash
   # Build and push Docker image
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin account.dkr.ecr.region.amazonaws.com
   docker build -t btc-trading-bot .
   docker tag btc-trading-bot:latest account.dkr.ecr.region.amazonaws.com/btc-trading-bot:latest
   docker push account.dkr.ecr.region.amazonaws.com/btc-trading-bot:latest

   # Create service
   aws ecs create-service --service-name btc-trading-bot --task-definition btc-trading-bot --desired-count 1 --launch-type FARGATE
   ```

### Google Cloud Run

1. **Deploy to Cloud Run**
   ```bash
   # Build and deploy
   gcloud builds submit --tag gcr.io/PROJECT-ID/btc-trading-bot
   gcloud run deploy btc-trading-bot \
     --image gcr.io/PROJECT-ID/btc-trading-bot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 1Gi \
     --cpu 1 \
     --max-instances 1 \
     --set-env-vars DEBUG=false
   ```

2. **Set Environment Variables**
   ```bash
   # Set secrets
   gcloud run services update btc-trading-bot \
     --set-env-vars GOOGLE_SHEET_ID=your_sheet_id \
     --set-secrets TELEGRAM_BOT_TOKEN=telegram-token:latest
   ```

---

## 🔒 Security Considerations

### Environment Variables
```bash
# Production .env (sensitive values should use secrets management)
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Use secrets management for sensitive data
GOOGLE_SHEET_ID_FILE=/run/secrets/google_sheet_id
TELEGRAM_BOT_TOKEN_FILE=/run/secrets/telegram_bot_token
```

### Secrets Management

#### Docker Secrets
```yaml
# docker-compose.prod.yml with secrets
version: '3.8'

secrets:
  google_sheet_id:
    file: ./secrets/google_sheet_id.txt
  telegram_bot_token:
    file: ./secrets/telegram_bot_token.txt

services:
  btc-trading-bot:
    # ... other config
    secrets:
      - google_sheet_id
      - telegram_bot_token
```

#### HashiCorp Vault
```bash
# Store secrets in Vault
vault kv put secret/btc-bot \
  google_sheet_id="your_sheet_id" \
  telegram_bot_token="your_token"

# Use Vault agent or init container to retrieve secrets
```

### Network Security

#### Reverse Proxy (Nginx)
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://btc-trading-bot:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://btc-trading-bot:8000;
    }
}
```

#### Firewall Rules
```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable

# iptables
iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

---

## 📊 Monitoring & Logging

### Application Monitoring

#### Health Checks
```bash
# Health check endpoint
curl https://your-domain.com/health

# Docker health check
docker inspect --format='{{json .State.Health}}' btc-trading-bot-prod
```

#### Prometheus Metrics
Add to `app/main.py`:
```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Centralized Logging

#### ELK Stack
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.6.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.6.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.6.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

#### Grafana Dashboard
```yaml
# grafana.yml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your_password
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

volumes:
  grafana_data:
```

---

## 🔄 Backup & Recovery

### Data Backup

#### Automated Backups
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/btc-bot"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup data directory
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C /opt/btc-trading-bot data/

# Backup configuration
cp /opt/btc-trading-bot/.env $BACKUP_DIR/env_$DATE.backup
cp /opt/btc-trading-bot/service_account.json $BACKUP_DIR/service_account_$DATE.json

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
find $BACKUP_DIR -name "*.json" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Cron Schedule
```bash
# crontab -e
# Daily backup at 2 AM
0 2 * * * /opt/btc-trading-bot/scripts/backup.sh >> /var/log/btc-bot-backup.log 2>&1
```

### Disaster Recovery

#### Recovery Process
```bash
# 1. Stop application
docker-compose -f docker-compose.prod.yml down

# 2. Restore data
tar -xzf /opt/backups/btc-bot/data_20240101_020000.tar.gz -C /opt/btc-trading-bot/

# 3. Restore configuration
cp /opt/backups/btc-bot/env_20240101_020000.backup /opt/btc-trading-bot/.env
cp /opt/backups/btc-bot/service_account_20240101_020000.json /opt/btc-trading-bot/service_account.json

# 4. Start application
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify recovery
curl http://localhost/health
```

---

## ⚡ Performance Optimization

### Resource Limits

#### Docker Resource Limits
```yaml
services:
  btc-trading-bot:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

#### Application Tuning
```python
# app/config.py - Production settings
class Settings(BaseSettings):
    # Connection pools
    max_connections: int = 20
    connection_timeout: int = 30

    # Caching
    cache_ttl: int = 300  # 5 minutes
    max_cache_size: int = 1000

    # Rate limiting
    rate_limit_per_minute: int = 60
```

### Database Optimization (Optional)

#### PostgreSQL for Production
```yaml
# docker-compose.prod.yml
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: btc_trading_bot
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf

volumes:
  postgres_data:
```

---

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs btc-trading-bot

# Check container status
docker ps -a

# Inspect container
docker inspect btc-trading-bot-prod
```

#### Memory Issues
```bash
# Check memory usage
docker stats btc-trading-bot-prod

# Increase memory limits
# Edit docker-compose.prod.yml
    deploy:
      resources:
        limits:
          memory: 2G
```

#### SSL Certificate Issues
```bash
# Check certificate
openssl x509 -in /path/to/cert.pem -text -noout

# Renew Let's Encrypt certificate
certbot renew --nginx
```

### Performance Issues
```bash
# Check application performance
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost/health"

# Monitor resource usage
htop
iotop
nethogs
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Health checks working
- [ ] Load testing completed

### Post-Deployment
- [ ] Application accessible
- [ ] Health endpoint responding
- [ ] Logs are being generated
- [ ] Monitoring alerts configured
- [ ] Backup tested
- [ ] Documentation updated

### Production Readiness
- [ ] Security hardening complete
- [ ] Performance optimized
- [ ] Scaling strategy defined
- [ ] Incident response plan ready
- [ ] Team training completed

---

**Production deployment complete! 🚀**

Monitor your application and maintain regular backups for a successful production environment.