# 📋 Sumário Técnico — vnstat Dashboard

## 📦 O que foi entregue

Uma **dashboard full-stack moderna** para monitorar tráfego de rede (`vnstat`) de múltiplos hosts com **autenticação JWT**, **gráficos interativos**, **MariaDB** e **deploy containerizado**.

---

## 🏗️ Arquitetura completa

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (SPA)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ login.html           dashboard.html     host.html        │  │
│  │ (500 linhas)         (800 linhas)       (600 linhas)     │  │
│  │ • Tema escuro        • KPIs              • Timeline 24h  │  │
│  │ • Glassmorphism      • Host cards        • Charts diários│  │
│  │ • CSS embutido       • Chart.js          • Gráficos mes │  │
│  │ • JS nativo (fetch)  • Responsive        │              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↑                                     │
│                         JWT/Cookie                              │
│                            ↓                                     │
├──────────────────────────────────────────────────────────────────┤
│                       NGINX (reverse proxy)                       │
├──────────────────────────────────────────────────────────────────┤
│                            ↑                                     │
│                       HTTP requests                              │
│                            ↓                                     │
├──────────────────────────────────────────────────────────────────┤
│                     FLASK BACKEND (Python)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /api/auth/*            /api/*              /api/collector│  │
│  │ • POST login           • GET overview      • POST push   │  │
│  │ • POST logout          • GET host/<name>   • GET status  │  │
│  │ • GET me               • GET chart/daily                 │  │
│  │                        • GET chart/monthly               │  │
│  │                        • GET hosts                       │  │
│  │                                                          │  │
│  │ routes/                models.py           __init__.py  │  │
│  │ • auth.py              • User              • Factory    │  │
│  │ • api.py               • Host              • Config     │  │
│  │ • collector.py         • TrafficSnapshot   • Extensions │  │
│  │ • pages.py             • TrafficDaily                    │  │
│  │                        • TrafficMonthly                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                     │
├──────────────────────────────────────────────────────────────────┤
│                      MARIADB (Database)                           │
│  • vnstat_dash database                                          │
│  • 5 tables (users, hosts, snapshots, daily, monthly)           │
│  • Indices on host_id, captured_at                              │
│  • Autoincrement primary keys                                    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┐
│  pi (Linux)  │ note (Linux) │ ser4ph-arm   │  ← MONITORED HOSTS
│              │              │  (Oracle)    │
│  collector.py (agent, cron 5min)           │
│  pushes vnstat --json to API                │
└──────────────┴──────────────┴──────────────┘
```

---

## 📁 Arquivos (23 no total)

### Backend (Python)
| Arquivo | LOC | Descrição |
|---------|-----|-----------|
| `backend/__init__.py` | 70 | App factory, config, seed |
| `backend/models.py` | 95 | SQLAlchemy ORM (5 models) |
| `backend/routes/auth.py` | 30 | Login/logout JWT |
| `backend/routes/api.py` | 180 | Data endpoints (overview, charts) |
| `backend/routes/collector.py` | 80 | Receiver para agents |
| `backend/routes/pages.py` | 25 | SPA routing |
| `wsgi.py` | 10 | Entry point (Gunicorn) |

**Total backend:** ~490 LOC Python (bem-estruturado)

### Frontend (HTML/CSS/JS)
| Arquivo | LOC | Descrição |
|---------|-----|-----------|
| `frontend/templates/login.html` | 500 | Login form, animações |
| `frontend/templates/dashboard.html` | 800 | Overview + charts |
| `frontend/templates/host.html` | 600 | Detalhe por host |

**Total frontend:** ~1900 LOC (CSS embutido, JS fetch nativo)

### Collector (Agents)
| Arquivo | LOC | Descrição |
|---------|-----|-----------|
| `collector/collector.py` | 150 | Agent script (vnstat parse + push) |
| `collector/install-collector.sh` | 60 | Deploy automático (cron setup) |

**Total collector:** ~210 LOC (Python + Bash)

### DevOps / Config
| Arquivo | Descrição |
|---------|-----------|
| `docker-compose.yml` | Stack (MariaDB, Flask, Nginx) |
| `Dockerfile` | Python 3.11 + Gunicorn |
| `nginx/nginx.conf` | Reverse proxy + SPA routing |
| `db/schema.sql` | DDL com indices + seed |
| `requirements.txt` | Deps Flask (8 packages) |
| `.gitignore` | Ignore padrão |
| `.env.example` | Template de vars |

### Documentação
| Arquivo | Descrição |
|---------|-----------|
| `README.md` | Overview, features, setup |
| `QUICKSTART.md` | 5-min guide (este é para você!) |
| `DEPLOYMENT.md` | Setup específico seu homelab |
| `API.md` | Docs de endpoints + exemplos cURL/Python |

### Scripts
| Arquivo | Descrição |
|---------|-----------|
| `setup.sh` | Interativo (gera .env, build Docker) |

---

## ⚙️ Stack Tecnológico

### Backend
```
Flask 3.0.0              — Web framework
Flask-SQLAlchemy 3.1.1   — ORM
Flask-JWT-Extended 4.5.3 — Auth com JWT
PyMySQL 1.1.0            — Driver MySQL
Gunicorn 21.2.0          — WSGI server
```

### Frontend
```
Chart.js 4.4.0  — Gráficos interativos
HTML5 + CSS3    — UI nativa (sem frameworks)
JavaScript ES6  — Fetch API, async/await
Google Fonts    — IBM Plex Mono + Inter
```

### Infrastructure
```
MariaDB 11.1    — Database
Docker          — Containerização
Nginx (Alpine)  — Reverse proxy
Python 3.11     — Runtime
```

---

## 🔐 Segurança implementada

✅ **JWT com HTTPOnly cookies** — CSRF-safe  
✅ **Senhas bcrypted** — Werkzeug.security  
✅ **Header X-Collector-Key** — Agent auth  
✅ **SQL injection protection** — SQLAlchemy ORM  
✅ **CORS/SOP** — Nginx isolamento  
✅ **Secure defaults** — JWT_COOKIE_SECURE em prod  
✅ **Session expiry** — 12h default  

---

## 📊 Features

### Dashboard Principal
```
✓ KPIs agregados (RX/TX total, mês, live)
✓ Host cards com status (online/offline)
✓ Gráfico 30 dias (bar, por host)
✓ Gráfico 12 meses (line, agregado)
✓ Refresh automático (30s)
✓ Responsive (mobile-first CSS)
```

### Host Detail
```
✓ Timeline últimas 24h (rate instantânea)
✓ Gráfico diário (30 dias)
✓ Gráfico mensal (12 meses)
✓ Estatísticas atuais (RX/TX total)
✓ Breadcrumb voltar
```

### Autenticação
```
✓ Login/logout
✓ JWT persistent (cookie)
✓ Session 12h expiry
✓ Usuário visível no header
```

### Dados
```
✓ Snapshots horários (últimas 24h)
✓ Agregação diária (última 30 dias)
✓ Agregação mensal (últimos 12 meses)
✓ Auto-upsert em collector push
✓ Indexed queries (rápidas)
```

---

## 🚀 Deployment

### Quick (5 min)
```bash
bash setup.sh          # Interactive setup
docker-compose up -d   # Start containers
# → http://localhost
```

### Production
```bash
# .env com senhas fortes
# TLS via Nginx Proxy Manager
# Backup automático do banco
# Rate limiting (opcional)
```

---

## 📈 Performance

**Tipicamente esperado:**
```
Hosts: 3
Intervalo coleta: 5 min
Retenção: 1 ano

DB size: ~100-150 MB (snapshots + daily + monthly)
Query /api/overview: <100ms
Query /api/chart/daily: <200ms
Page load: <1s (gzip enabled)
```

**Escalabilidade:**
- Índices em (host_id, captured_at)
- Snapshots são writes-only (insert), nunca update
- Daily/monthly são upserts (small dataset)
- Nginx gzip + caching headers

---

## 🎨 Design

### Cores (CSS vars)
```
--bg:        #0a0e14  (almost black)
--surface:   #0f1520  (dark blue)
--border:    #1e293b  (slate)
--accent:    #38bdf8  (cyan)
--accent2:   #34d399  (green)
--tx:        #f472b6  (pink)
--rx:        #38bdf8  (blue)
--text:      #e2e8f0  (light)
--muted:     #64748b  (gray)
```

### Tipografia
```
Monospace: IBM Plex Mono (labels, valores)
Sans:      Inter (headers, UI)
Gzip:      Todos assets comprimidos
```

### Componentes
```
KPI Cards     → glassmorphism, hover glow
Host Cards    → status dot pulsing, click-through
Charts        → Chart.js com tooltips customizados
Login Form    → grid background, gradient button
Header        → fixed, sticky nav
```

---

## 🔄 Fluxo de dados

```
1. Collector (a cada 5 min em cada host)
   ↓
   vnstat --json (lê interface)
   ↓
   Parser (extrai totais, daily, monthly)
   ↓
   HTTP POST /api/collector/push
   
2. Backend recebe push
   ↓
   Valida X-Collector-Key
   ↓
   Insere/upsert em tabelas (atomic)
   ↓
   MariaDB commit
   
3. Frontend (user action)
   ↓
   Fetch /api/overview (JWT)
   ↓
   Backend queries banco (indexed)
   ↓
   JSON response
   ↓
   Chart.js renderiza gráficos
```

---

## 🧪 Teste manual

```bash
# 1. Login
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}' \
  -c cookies.txt

# 2. Overview
curl http://localhost/api/overview \
  -b cookies.txt | jq .

# 3. Collector mock push
curl -X POST http://localhost/api/collector/push \
  -H "X-Collector-Key: seu_collector_key" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "test-host",
    "interface": "eth0",
    "captured_at": "2024-01-15T14:30:00+00:00",
    "rx_total": 1000000000,
    "tx_total": 800000000,
    "rx_hour": 100000000,
    "tx_hour": 80000000,
    "rx_rate": 262144,
    "tx_rate": 131072,
    "days": [],
    "months": []
  }'
```

---

## 📋 Checklist pós-setup

- [ ] Dashboard acessível em http://seu_ip
- [ ] Login funciona (admin / sua_senha)
- [ ] Overview carrega sem erro 404
- [ ] Coletores instalados em pi, note, ser4ph-arm
- [ ] `/opt/vnstat-collector/run.sh` retorna "Pushed OK"
- [ ] Cron está agendado (`crontab -l`)
- [ ] Dados aparecem ~10 min depois (snapshots no banco)
- [ ] Gráficos renderizam (Chart.js)
- [ ] Host detail page funciona
- [ ] Logout funciona

---

## 🆘 Troubleshooting rápido

| Problema | Solução |
|----------|---------|
| 404 no login | Verificar `HOSTS` no .env |
| Sem dados no dashboard | Aguardar 10 min + verificar cron |
| Collector connection refused | Verificar IP Tailscale correto |
| Mariadb crashed | `docker-compose down && rm -rf mariadb_data/ && up -d` |
| JWT expirado | Fazer login novo |
| Gráficos vazios | Dados ainda não agregados (5+ min) |

---

## 📚 Documentação associada

| Doc | Propósito |
|-----|-----------|
| **README.md** | Overview + features + install |
| **QUICKSTART.md** | 5-min setup guide |
| **DEPLOYMENT.md** | Setup específico homelab |
| **API.md** | Endpoints + exemplos cURL/Python |
| **Este arquivo** | Sumário técnico |

---

## 🎯 Próximas iterações (ideias)

```
[ ] Alertas por limiar (email/Telegram)
[ ] Export CSV/PDF
[ ] Integração Prometheus
[ ] Mobile app native
[ ] Previsão de tráfego (ML)
[ ] Múltiplas interfaces por host
[ ] Rate limiting (Flask-Limiter)
[ ] Audit log (quem fez login quando)
[ ] Dark/light theme toggle
[ ] Documentação Swagger/OpenAPI
```

---

## 💡 Decisões de design

✅ **Flask over FastAPI** → Familiaridade, TLP scripts já usam  
✅ **MariaDB over SQLite** → Escalabilidade, replicação possível  
✅ **JWT em cookies** → Secure, SameSite CSRF protection  
✅ **Collector push** → Agent leve, server não precisa SSH  
✅ **Chart.js** → Sem framework frontend, JavaScript puro  
✅ **Docker** → Zero-config, reproducible, pronto pra produção  
✅ **Nginx reverse proxy** → TLS, gzip, load balancing (future)  

---

## 📞 Suporte

Veja `DEPLOYMENT.md` para seu setup específico (Oracle ARM + 3 hosts).  
Veja `API.md` para programar contra a API.  
Veja `QUICKSTART.md` para começar agora.

---

**Desenvolvido com ❤️ — Pronto para usar. Deploy em 5 minutos.**

