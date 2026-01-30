# Production Deployment Guide

**Repository**: https://github.com/jcmvstard-prog/customs-kb

This guide covers deploying the US Customs Knowledge Base to production.

---

## Quick Deploy Options

### Option 1: Railway.app (Recommended - Easiest)

Railway has the best Docker Compose support and free tier.

**Steps:**

1. Go to https://railway.app/
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `jcmvstard-prog/customs-kb`
5. Railway will detect `docker-compose.yml` and deploy all services
6. Add environment variables in Railway dashboard:
   - `POSTGRES_PASSWORD` (generate secure password)
   - All other vars use defaults from `.env.example`
7. Click "Deploy"

**Cost**: Free tier (500 hours/month, $5 credit)

---

### Option 2: Render.com (Good Alternative)

**Steps:**

1. Go to https://render.com/
2. Sign in with GitHub
3. Create PostgreSQL Database:
   - Click "New" → "PostgreSQL"
   - Name: `customs-kb-db`
   - Plan: Free
   - Copy connection details
4. Create Qdrant Service:
   - Click "New" → "Private Service"
   - Docker Image: `qdrant/qdrant:v1.7.4`
   - Plan: Free
   - Disk: 1GB at `/qdrant/storage`
5. Create Application:
   - Click "New" → "Web Service"
   - Connect to `customs-kb` repo
   - Build: `pip install -r requirements.txt`
   - Start: `python -m src.cli.main ingest status`
   - Add environment variables (from PostgreSQL and Qdrant services)

**Cost**: Free tier available

---

### Option 3: Fly.io (Best for Docker Compose)

**Steps:**

1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `flyctl auth login`
3. Launch app:
   ```bash
   cd ~/my-new-project/customs-kb
   flyctl launch --no-deploy
   ```
4. Create volumes:
   ```bash
   flyctl volumes create postgres_data --size 1
   flyctl volumes create qdrant_data --size 1
   ```
5. Deploy:
   ```bash
   flyctl deploy
   ```

**Cost**: Free tier (3 shared-cpu-1x, 3GB storage)

---

### Option 4: DigitalOcean App Platform

**Steps:**

1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App" → GitHub → Select `customs-kb`
3. Configure services:
   - **PostgreSQL**: Add managed database ($15/mo or $0 with credit)
   - **App**: Python worker, run `python -m src.cli.main ingest status`
4. Add environment variables
5. Click "Deploy"

**Cost**: $5/mo for basic app + $15/mo for managed DB (60-day free credit available)

---

### Option 5: Docker Compose on VPS (Full Control)

If you have a VPS (DigitalOcean Droplet, AWS EC2, etc.):

```bash
# On your VPS
git clone https://github.com/jcmvstard-prog/customs-kb.git
cd customs-kb
cp .env.example .env
# Edit .env with secure passwords
docker-compose up -d
```

**Cost**: VPS pricing ($5-10/mo)

---

## Environment Variables Required

```bash
# PostgreSQL
POSTGRES_HOST=<db-host>
POSTGRES_PORT=5432
POSTGRES_DB=customs_kb
POSTGRES_USER=customs_user
POSTGRES_PASSWORD=<secure-password>

# Qdrant
QDRANT_HOST=<qdrant-host>
QDRANT_PORT=6333
QDRANT_COLLECTION=cbp_documents

# Application
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
FEDERAL_REGISTER_AGENCY=u-s-customs-and-border-protection
LOG_LEVEL=INFO
```

---

## Post-Deployment Steps

### 1. Initialize Databases

SSH into your deployment or run via platform's console:

```bash
# Initialize PostgreSQL schema
python scripts/init_db.py

# Initialize Qdrant collection
python scripts/init_qdrant.py
```

### 2. Ingest Sample Data

```bash
# Load HTS codes
python -m src.cli.main ingest htsus

# Load Federal Register documents (last 3 months)
python -m src.cli.main ingest federal-register \
    --start-date 2024-10-01 \
    --end-date 2024-12-31
```

### 3. Verify Deployment

```bash
# Check system status
python -m src.cli.main ingest status

# Test query
python -m src.cli.main query hts-lookup "cheese"
```

---

## Monitoring

### Health Checks

The application includes health checks:
- PostgreSQL connection test
- Qdrant availability check
- Embedding model loaded

### Logs

Access logs via your platform:
- Railway: `railway logs`
- Render: View in dashboard
- Fly.io: `flyctl logs`

### Metrics

Key metrics to monitor:
- Database size
- Vector collection size
- Ingestion run history
- Query response times

---

## Scaling

### Horizontal Scaling

For production load:
1. Scale PostgreSQL to managed service (Render, Railway, or RDS)
2. Scale Qdrant with cluster mode
3. Add multiple app instances behind load balancer
4. Use Redis for caching (optional)

### Data Growth

- PostgreSQL: ~1GB per 10,000 documents
- Qdrant: ~200MB per 10,000 documents (384-dim vectors)
- Plan storage accordingly

---

## Security

### Production Checklist

- [ ] Use strong passwords for databases
- [ ] Enable SSL/TLS for database connections
- [ ] Set `LOG_LEVEL=WARNING` in production
- [ ] Enable firewall rules (only allow necessary ports)
- [ ] Regular backups of PostgreSQL
- [ ] Backup Qdrant volumes
- [ ] Rotate API tokens if using external services

### Secrets Management

Use platform's secret manager:
- Railway: Environment variables (encrypted)
- Render: Secret files
- Fly.io: `flyctl secrets`

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# Restore
psql -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB < backup.sql
```

### Qdrant Backup

```bash
# Backup Qdrant snapshots
curl -X POST "http://$QDRANT_HOST:$QDRANT_PORT/collections/cbp_documents/snapshots"

# Download snapshot
curl "http://$QDRANT_HOST:$QDRANT_PORT/collections/cbp_documents/snapshots/{snapshot_name}" \
    --output snapshot.qdrant
```

---

## Cost Estimates

### Free Tier (Development/POC)
- **Railway**: Free ($5 credit/mo)
- **Render**: Free (PostgreSQL + 2 services)
- **Fly.io**: Free (3 VMs + 3GB storage)

### Production (Low Traffic)
- **Railway**: $5-15/mo
- **Render**: $7-20/mo (managed PostgreSQL)
- **DigitalOcean**: $10-25/mo (App + managed DB)
- **AWS/GCP**: $20-50/mo (EC2/Compute + RDS)

### Production (High Traffic)
- App: $50-100/mo (multiple instances)
- PostgreSQL: $50-200/mo (managed, HA)
- Qdrant: $100-300/mo (cluster mode)
- Total: $200-600/mo for high-availability setup

---

## Support

- GitHub Issues: https://github.com/jcmvstard-prog/customs-kb/issues
- Documentation: See README.md, QUICKSTART.md, TROUBLESHOOTING.md

---

## Next Steps

1. Choose a deployment platform (Railway recommended for easiest start)
2. Deploy services
3. Initialize databases
4. Ingest data
5. Set up monitoring
6. Configure backups
7. Plan for scaling

**Deployment Date**: January 30, 2026
**Status**: Ready for Production
