# Deployment Guide

## Deployment Strategies

### 1. Docker Compose (Single Server)

Best for: Development, small teams, single-node deployments

**Steps:**
```bash
# Clone repository
git clone <repository-url>
cd build-agent

# Create production environment file
cp backend/.env.example backend/.env
# Edit with production values

# Deploy
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f backend
```

### 2. Kubernetes (Production Scale)

Best for: High availability, auto-scaling, enterprise deployments

**Prerequisites:**
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x installed

**Deployment:**
```bash
# Create namespace
kubectl create namespace buildagent

# Deploy PostgreSQL
kubectl apply -f k8s/postgres.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml

# Deploy ChromaDB
kubectl apply -f k8s/chromadb.yaml

# Deploy Backend
kubectl apply -f k8s/backend.yaml

# Deploy Frontend
kubectl apply -f k8s/frontend.yaml

# Verify
kubectl get pods -n buildagent
kubectl get services -n buildagent
```

**Sample Kubernetes Manifests:**

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: buildagent-backend
  namespace: buildagent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: buildagent/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: buildagent
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### 3. Cloud Deployment

#### AWS Deployment

**Using ECS (Elastic Container Service):**
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name buildagent

# Register task definitions
aws ecs register-task-definition --cli-input-json file://aws/ecs-task.json

# Create service
aws ecs create-service \
  --cluster buildagent \
  --service-name backend \
  --task-definition buildagent-backend \
  --desired-count 2
```

**Using EKS (Elastic Kubernetes Service):**
```bash
# Create EKS cluster
eksctl create cluster --name buildagent --region us-east-1

# Deploy
kubectl apply -f k8s/
```

#### GCP Deployment

**Using GKE (Google Kubernetes Engine):**
```bash
# Create cluster
gcloud container clusters create buildagent \
  --zone us-central1-a \
  --num-nodes 3

# Deploy
kubectl apply -f k8s/
```

#### Azure Deployment

**Using AKS (Azure Kubernetes Service):**
```bash
# Create cluster
az aks create \
  --resource-group buildagent \
  --name buildagent-cluster \
  --node-count 3

# Deploy
kubectl apply -f k8s/
```

## SSL/TLS Configuration

### Using Let's Encrypt

**With Nginx:**
```nginx
server {
    listen 443 ssl;
    server_name api.buildagent.com;

    ssl_certificate /etc/letsencrypt/live/api.buildagent.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.buildagent.com/privkey.pem;

    location / {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**With Traefik:**
```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@buildagent.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt

  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.buildagent.com`)"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
```

## Database Migration

### Using Alembic

```bash
# Initialize migrations
cd backend
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Run migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backup Strategy

```bash
# PostgreSQL backup
docker exec buildagent-postgres pg_dump -U postgres buildagent > backup.sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec buildagent-postgres pg_dump -U postgres buildagent | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'buildagent'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Alerting Rules

```yaml
# alert_rules.yml
groups:
  - name: buildagent
    rules:
      - alert: HighErrorRate
        expr: rate(buildagent_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: AgentDown
        expr: up{job="buildagent"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "BuildAgent is down"
```

### Grafana Dashboard Import

1. Navigate to Grafana (http://localhost:3000)
2. Go to Dashboards > Import
3. Upload `docker/grafana/dashboards/dashboard.json`
4. Select Prometheus datasource

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Load Balancing

**Nginx Load Balancer:**
```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

## Security Hardening

### Firewall Rules

```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### Docker Security

```bash
# Run with non-root user
useradd -m buildagent
sudo usermod -aG docker buildagent

# Limit container resources
docker run --memory=2g --cpus=2 buildagent/backend
```

### Secrets Management

**Using Docker Secrets:**
```bash
# Create secrets
echo "my-secret-key" | docker secret create api_key -
echo "db-password" | docker secret create db_password -

# Use in compose
docker-compose -f docker-compose.secrets.yml up
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest backend/tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push
        run: |
          docker build -t buildagent/backend:${{ github.sha }} backend/
          docker push buildagent/backend:${{ github.sha }}
      - name: Deploy to production
        run: |
          ssh user@server "docker pull buildagent/backend:${{ github.sha }} && docker-compose up -d"
```

## Rollback Strategy

```bash
# Docker Compose rollback
docker-compose pull
docker-compose up -d

# Kubernetes rollback
kubectl rollout undo deployment/backend

# Database rollback
alembic downgrade -1
```

## Maintenance

### Log Rotation

```bash
# Configure logrotate
/etc/logrotate.d/buildagent
/var/log/buildagent/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 buildagent buildagent
}
```

### Health Monitoring

```bash
# Cron job for health checks
*/5 * * * * /usr/local/bin/health-check.sh || /usr/local/bin/alert.sh
```
