# vnstat Dashboard — Modern Network Traffic Monitoring

Uma dashboard moderna, responsiva e com práticas atuais para monitorar tráfego de rede via `vnstat` de múltiplos hosts com:

- 🔐 **Autenticação JWT** com cookies seguros
- 📊 **Gráficos interativos** com Chart.js (dia, mês, agregado)
- 🎨 **UI moderna** — tema escuro, glassmorphism, design de infra
- 📡 **Arquitetura escalável** — Python + Flask + MariaDB
- ⚙️ **Deploy containerizado** — Docker Compose pronto para produção
- 📈 **Métricas agregadas** — totais cumulativos + histórico granular

---

## 🏗️ Arquitetura

```
hosts (pi, note, ser4ph-arm)
    ↓ cron (a cada 5min)
collector.py (pushes vnstat JSON)
    ↓ HTTP POST
MariaDB (vnstat_dash)
    ↓
Flask API (/api/*)
    ↓
Nginx (reverse proxy)
    ↓
Frontend SPA (login + dashboard + host detail)
```

**Fluxo de dados:**
1. **Collector Agent** roda em cada host via cron
2. Lê `vnstat --json` (interfaces, tráfego diário/mensal)
3. POSTs para `/api/collector/push` com autenticação `X-Collector-Key`
4. Backend normaliza e upserts em tabelas (snapshots, daily, monthly)
5. Frontend fetch `/api/*` (JWT protegido) para renderizar gráficos + KPIs

---

## 🚀 Quick Start

### 1. Clonar e configurar variáveis de ambiente

```bash
git clone <repo> vnstat-dashboard
cd vnstat-dashboard
cp .env.example .env
```

Editar `.env`:
```bash
SECRET_KEY=seu_secret_aleatorio_aqui_32_chars_min
JWT_SECRET_KEY=outro_secret_aleatorio_diferente
DATABASE_URL=mysql+pymysql://vnstat:SENHA@db:3306/vnstat_dash
COLLECTOR_API_KEY=sua_chave_de_coletor_aqui
ADMIN_USER=admin
ADMIN_PASS=mudar_em_producao
HOSTS="pi:Raspberry Pi:100.x.x.1,note:Note (Debian):100.x.x.2,ser4ph-arm:Oracle ARM:100.x.x.3"
```

### 2. Build e start (no servidor/VPS)

```bash
docker-compose up -d
```

Aguarde ~30s:
```bash
docker-compose logs -f app
```

Quando ver `Listening on`, acessar:
```
http://seu_servidor:80
```

Login:
- Usuário: `admin`
- Senha: `mudar_em_producao` (mude no `.env`!)

### 3. Instalar coletores em cada host

No **pi** (exemplo):
```bash
# Copiar collector pro host
scp -r collector/ pi:/tmp/vnstat-collector-install/
ssh pi

# No pi:
cd /tmp/vnstat-collector-install
sudo bash install-collector.sh \
  pi \
  "http://100.x.x.x:5000" \
  "sua_chave_de_coletor_aqui" \
  "eth0"
```

Repetir para `note`, `ser4ph-arm` (ajustar IP da interface).

**Test:**
```bash
/opt/vnstat-collector/run.sh
# → [2024-...] Pushed OK — {"ok": true, "host": "pi"}
```

Cron starts automatically — check:
```bash
crontab -l | grep vnstat
tail -f /var/log/vnstat-collector.log
```

---

## 📊 Features

### Dashboard principal
- **KPIs agregados:** Total RX/TX (cumulative), taxa live, totais do mês
- **Host cards:** Status online/offline, totais por host, taxa atual
- **Gráficos:**
  - Últimos 30 dias (barras, por host, RX/TX separado)
  - Últimos 12 meses (linhas, agregado)

### Página de host individual
- Estatísticas atuais (RX/TX total)
- Timeline últimas 24h (taxa instantânea)
- Gráfico diário (30 dias)
- Gráfico mensal (12 meses)

### Autenticação
- Login/logout com JWT
- Cookies seguros (`HttpOnly`, `Secure` em HTTPS)
- Sessions auto-expirável (default: 12h)

---

## 🔧 Endpoints da API

### Auth
```
POST   /api/auth/login          body: {username, password}
POST   /api/auth/logout
GET    /api/auth/me             → {id, username}
```

### Data (JWT required)
```
GET    /api/overview                     → KPIs + host status
GET    /api/hosts                        → lista de hosts
GET    /api/host/<name>                  → detalhe de 1 host
GET    /api/chart/daily?days=30&hosts=pi,note
GET    /api/chart/monthly
```

### Collector (X-Collector-Key required)
```
POST   /api/collector/push               body: vnstat payload
GET    /api/collector/status             health check
```

---

## 📁 Estrutura de arquivos

```
vnstat-dashboard/
├── backend/
│   ├── __init__.py              # app factory
│   ├── models.py                # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py              # login/logout
│   │   ├── api.py               # data endpoints
│   │   ├── collector.py         # receiver push
│   │   └── pages.py             # SPA routes
│   └── utils/
├── frontend/
│   ├── templates/
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   └── host.html
│   └── static/
├── collector/
│   ├── collector.py             # agent script
│   └── install-collector.sh
├── db/
│   └── schema.sql               # MariaDB init
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── wsgi.py
└── .gitignore
```

---

## 🔐 Segurança (produção)

1. **Alterar senhas padrão:**
   ```bash
   # No .env
   ADMIN_PASS=senhaForte32caractersAqui
   MYSQL_ROOT_PASSWORD=outraSenhaForte
   MYSQL_PASSWORD=vnstatSenhaForte
   ```

2. **HTTPS via Nginx Proxy Manager / Cloudflare:**
   - Expor porta 443 com certificado SSL
   - JWT `Secure` flag já ativado em prod

3. **Limitar colectores:**
   - COLLECTOR_API_KEY única, complexa
   - Validação de host_name (whitelist via DB)

4. **Rate limiting (opcional):**
   - Adicionar `Flask-Limiter` nos endpoints

---

## 🐛 Troubleshooting

### Collector não conecta
```bash
# Verificar conectividade Tailscale
ping 100.x.x.x

# Test POST manual
curl -X POST http://100.x.x.x:5000/api/collector/status \
  -H "X-Collector-Key: CHAVE_AQUI"
# → {"ok": true, "ts": "..."}

# Logs
tail -f /var/log/vnstat-collector.log
```

### Dashboard sem dados
```bash
# Verificar banco
docker-compose exec db mariadb -u vnstat -p vnstat_dash
> SELECT COUNT(*) FROM traffic_snapshots;

# Logs Flask
docker-compose logs app
```

### Gráficos vazios
- Aguarde 5+ minutos (colector roda a cada 5 min)
- Checar se hosts têm dados: `/api/overview`

---

## 🎨 Customização

### Alterar cores do tema
Em `frontend/templates/*.html`, editar `:root`:
```css
:root {
  --accent: #38bdf8;    /* ciano */
  --accent2: #34d399;   /* verde */
  --accent3: #818cf8;   /* roxo */
  --rx: #38bdf8;        /* download azul */
  --tx: #f472b6;        /* upload rosa */
}
```

### Adicionar novo host
Editar `.env`:
```bash
HOSTS="pi:...,note:...,novo_host:Display Name:100.x.x.4"
```

Ou via SQL:
```sql
INSERT INTO hosts (name, display_name, tailscale_ip)
  VALUES ('novo', 'Novo Host', '100.x.x.4');
```

### Mudar intervalo de coleta
No cron de cada host:
```bash
# A cada 1 min (mais frequente = mais dados)
* * * * * /opt/vnstat-collector/run.sh

# A cada 10 min (menos dados, menos carga)
*/10 * * * * /opt/vnstat-collector/run.sh
```

---

## 📋 Requisitos

- **Server:** Docker + Docker Compose
- **Hosts monitorados:** vnstat instalado, Python 3.7+, requests lib
- **Network:** Tailscale ou acesso direto entre hosts e server
- **Disco:** ~100MB para MariaDB (1 ano com 5min intervalo)

---

## 📝 Licença

MIT — use livremente!

---

## 🤝 Contribuições

PRs welcome! Ideias:
- Alertas por limiar de tráfego
- Export CSV/PDF
- Integração com Prometheus
- Mobile app
- Previsão via ML

---

**Desenvolvido com ❤️ por NemiK**

Dúvidas? Abra uma issue!
