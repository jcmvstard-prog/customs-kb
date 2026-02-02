# Quick Start Guide - US Customs Knowledge Base + Claude Code

## ✅ What's Installed

Your US Customs Knowledge Base is fully operational with:

- **3,958** Federal Register documents (1994-2026)
- **29,851** HTSUS tariff codes (complete 2025 schedule)
- **3,937** vector embeddings
- **FastAPI REST API** on http://localhost:8000
- **Web Dashboard** on http://localhost:8000/dashboard
- **Claude Code Integration** via helper scripts

## 🚀 Start Using Now

### 1. Start the API Server (if not running)

```bash
cd ~/my-new-project/customs-kb
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
```

### 2. Test It Works

```bash
# Quick status check
curl http://localhost:8000/api/status

# Or use the helper script
~/my-new-project/customs-kb/scripts/query_kb.sh status
```

### 3. Ask Claude Code Questions

**Just talk to Claude naturally! Examples:**

```
You: "What are the import duties for fresh cheese?"
Claude: [Uses query_kb.sh to search HTS codes and documents]

You: "Find recent CBP rulings about steel antidumping"
Claude: [Uses query_kb.sh to search Federal Register]

You: "Show me tariff codes for automobiles"
Claude: [Uses query_kb.sh to search HTS codes]
```

## 📋 Helper Script Commands

```bash
# Search customs documents
~/my-new-project/customs-kb/scripts/query_kb.sh search "textile quotas"

# Search tariff codes
~/my-new-project/customs-kb/scripts/query_kb.sh hts "electronics"

# Get specific HTS code details
~/my-new-project/customs-kb/scripts/query_kb.sh hts-detail "8703.10.00"

# Get document by number
~/my-new-project/customs-kb/scripts/query_kb.sh document "2024-28582"

# System status
~/my-new-project/customs-kb/scripts/query_kb.sh status

# Health check
~/my-new-project/customs-kb/scripts/query_kb.sh health
```

## 🌐 Direct API Access

```bash
# Search documents
curl "http://localhost:8000/api/search?q=steel+duties&limit=5"

# Search HTS codes
curl "http://localhost:8000/api/hts/search?q=cheese&limit=5"

# Get HTS code details
curl "http://localhost:8000/api/hts/0406.10.00"

# Get document details
curl "http://localhost:8000/api/documents/2024-28582"

# System status
curl "http://localhost:8000/api/status"
```

## 📱 Web Dashboard

Open in your browser: http://localhost:8000/dashboard

Features:
- Semantic search
- HTS code lookup
- Hybrid search (combine filters)
- Live statistics

## 📚 Documentation

- **Project README**: `~/my-new-project/customs-kb/README.md`
- **Claude Instructions**: `~/my-new-project/customs-kb/CLAUDE.md`
- **Home Directory Config**: `/Users/james/CLAUDE.md` (includes customs KB)
- **API Docs**: http://localhost:8000/docs (when server running)

## 🔧 Troubleshooting

**API not responding?**
```bash
# Check if server is running
ps aux | grep uvicorn

# Restart server
cd ~/my-new-project/customs-kb
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
```

**Database not connected?**
```bash
# Start Docker services
cd ~/my-new-project/customs-kb
docker-compose up -d
```

**Need to re-ingest data?**
```bash
cd ~/my-new-project/customs-kb
source venv/bin/activate

# Federal Register
python -m src.cli.main ingest federal-register --start-date 1994-01-01

# HTSUS
python -m src.cli.main ingest htsus
```

## 💡 Example Use Cases

**Import/Export Planning:**
```
"What are the duty rates for importing steel from China?"
"Find regulations about textile quotas"
"Show me HTS codes for electronic components"
```

**Compliance Research:**
```
"What are CBP requirements for food imports?"
"Find recent notices about trade agreements"
"Show antidumping duties for aluminum products"
```

**Tariff Classification:**
```
"Find the correct HTS code for dairy products"
"What's the difference between HTS 8703 and 8704?"
"Show all tariff codes for motor vehicles"
```

---

## ✨ You're All Set!

Your customs knowledge base is:
- ✅ Fully loaded with data
- ✅ API server ready
- ✅ Web dashboard accessible
- ✅ Integrated with Claude Code
- ✅ Helper scripts installed
- ✅ Documented in `/Users/james/CLAUDE.md`

**Just ask Claude Code your customs questions and it will automatically query the knowledge base!**
