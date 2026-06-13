# 🚀 vnstat Dashboard — Quick Start (5 minutos)

**Você está aqui:** Pronto para começar? Siga este guia rápido.

---

## ✅ O que você vai ter

Uma dashboard bonita com:
- 🔐 Login seguro com JWT
- 📊 Gráficos interativos (30 dias + 12 meses)
- 📡 Agregação automática de 3+ hosts
- ⚡ Atualização live a cada 5 minutos
- 🎨 UI moderna, tema escuro, responsivo

**Em números:**
- ✨ 3 templates HTML (login, dashboard, host detail)
- 🐍 7 arquivos Python (models, routes, factory)
- 🐳 Docker Compose (zero config de infra)
- 📚 4 docs (README, DEPLOYMENT, API, este)

---

## 🏃 5 Minutos de Setup

### Pré-requisitos

- Docker + Docker Compose instalados
- Acesso ao seu servidor (Oracle ARM VPS recomendado)
- vnstat instalado nos hosts que quer monitorar

### 1️⃣ Clone o projeto

```bash
cd /opt
git clone <seu-repo> vnstat-dashboard
cd vnstat-dashboard
```

### 2️⃣ Executar setup interativo

```bash
bash setup.sh
```

Vai:
1. Gerar secrets seguros automaticamente
2. Pedir credenciais admin (username/password)
3. Criar `.env` com tudo configurado
4. Build + start Docker containers

**Tempo:** ~2 min (primeira build)

### 3️⃣ Verificar se está rodando

```bash
docker-compose ps
# Deve mostrar 3 containers: db, app, web
```

Acessar:
```
http://seu_servidor:80
```

Login:
- Usuário: `admin` (ou o que você escolheu)
- Senha: (a que você digitou)

✅ **Dashboard pronta! Ainda sem dados (normal, aguarde coletores).**

---

## 📡 Instalar Coletores (2 min por host)

No **Raspberry Pi** (exemplo):

```bash
ssh pi@100.x.x.1

# Copiar collector pro host
scp -r /opt/vnstat-dashboard/collector/ pi:~/vnstat-collector

# Instalar
cd ~/vnstat-collector
COLLECTOR_KEY=$(grep COLLECTOR_API_KEY /opt/vnstat-dashboard/.env | cut -d= -f2)
sudo bash install-collector.sh pi "http://100.x.x.4" "$COLLECTOR_KEY" "eth0"
```

**Repetir para:**
- `note` (interface: `enp2s0`)
- `ser4ph-arm` (interface: `eth0`)

**Testar:**
```bash
/opt/vnstat-collector/run.sh
# → [2024-...] Pushed OK — {"ok": true, "host": "pi"}
```

✅ **Dados começam a aparecer em ~5 minutos.**

---

## 📊 O que você vai ver

### Dashboard Principal (overview)
```
┌─────────────────────────────────────────┐
│ vnstat-dashboard                        │
├─────────────────────────────────────────┤
│ AGREGADO TOTAL                          │
│ ┌─────────────────────────────────────┐ │
│ │ Total Recebido: 250 GB              │ │
│ │ Total Enviado:  180 GB              │ │
│ │ Total Mês:      42 GB               │ │
│ │ Taxa ao Vivo:   2.5 MB/s ↓ + 1 MB/s↑│ │
│ └─────────────────────────────────────┘ │
│                                         │
│ HOSTS                                   │
│ ┌───────────┐ ┌───────────┐ ┌────────┐│
│ │ Raspberry │ │ Note      │ │ Oracle ││
│ │ Pi (✓)    │ │(Debian)✓  │ │(ARM) ✓ ││
│ │ 120 GB ↓  │ │ 90 GB ↓   │ │ 40 GB↓ ││
│ │ 80 GB ↑   │ │ 60 GB ↑   │ │ 40 GB↑ ││
│ └───────────┘ └───────────┘ └────────┘│
│                                         │
│ GRÁFICOS                                │
│ [Linha 30 dias]   [Linha 12 meses]    │
└─────────────────────────────────────────┘
```

### Host Detail (exemplo: pi)
```
Estatísticas Atuais:
  RX Total: 120 GB
  TX Total: 80 GB

Últimas 24h: gráfico de taxa instantânea
Últimos 30 dias: barras por dia
Últimos 12 meses: linhas por mês
```

---

## 🔧 Arquitetura (alta visão)

```
Collector (cron 5min)
    ↓ (SSH/Tailscale)
vnstat --json
    ↓ (HTTP POST)
/api/collector/push ← MariaDB
    ↓
Front fetch /api/overview
    ↓
Chart.js renderiza gráficos
```

**Segurança:**
- JWT em cookies (HTTPOnly)
- Collector autenticado por header X-Collector-Key
- Senhas bcrypted no banco

---

## 📁 Arquivos principais

```
vnstat-dashboard/
├── backend/
│   ├── __init__.py          ← Factory Flask
│   ├── models.py            ← SQLAlchemy (Host, Snapshot, Daily, Monthly)
│   └── routes/
│       ├── auth.py          ← Login/logout
│       ├── api.py           ← /api/overview, /api/chart/*
│       ├── collector.py     ← POST /api/collector/push
│       └── pages.py         ← Templates rendering
├── frontend/templates/
│   ├── login.html           ← 500 linhas, CSS + JS embutido
│   ├── dashboard.html       ← 800 linhas, Chart.js + fetch API
│   └── host.html            ← 600 linhas, detalhe por host
├── collector/
│   ├── collector.py         ← Agent (roda em cada host)
│   └── install-collector.sh ← Deploy automático
├── docker-compose.yml       ← Stack completa
├── Dockerfile               ← Python 3.11 + Gunicorn
└── requirements.txt         ← Flask, SQLAlchemy, JWT...
```

---

## 🎨 Customizações comuns

### Mudar cores do tema

Em qualquer template HTML, editar `:root`:

```css
:root {
  --accent: #38bdf8;    /* azul cyan */
  --tx: #f472b6;        /* rosa */
  --bg: #0a0e14;        /* quase preto */
}
```

### Adicionar novo host

No `.env`:
```bash
HOSTS="pi:...,note:...,novo:Display Name:100.x.x.5"
```

Ou via SQL (banco já está rodando):
```bash
docker-compose exec db mariadb -u vnstat -p vnstat_dash
INSERT INTO hosts (name, display_name, tailscale_ip) VALUES ('novo', 'Novo Host', '100.x.x.5');
```

### Mudar frequência de coleta

Em cada host, editar crontab:
```bash
# A cada 1 min (mais dados)
* * * * * /opt/vnstat-collector/run.sh

# A cada 10 min (menos dados)
*/10 * * * * /opt/vnstat-collector/run.sh
```

### HTTPS via Nginx Proxy Manager

1. Em `npm.nemik.top`, criar Proxy Host
2. Domain: `vnstat.nemik.top`
3. Forward para: `seu_servidor:80` (ou IP Docker interno)
4. SSL: Cloudflare/Let's Encrypt

Pronto — acesso via HTTPS!

---

## 🐛 Primeiros problemas (como resolver)

### "Sem dados no dashboard" (30 min depois)

```bash
# 1. Verificar se coletores estão conectando
docker-compose exec db mariadb -u vnstat -p vnstat_dash
> SELECT COUNT(*) FROM traffic_snapshots;
# Se = 0: coletores não chegaram

# 2. Testar collector manualmente
ssh pi@100.x.x.1
/opt/vnstat-collector/run.sh
# Deve mostrar: Pushed OK

# 3. Se erro, verificar conectividade
ping 100.x.x.4
curl http://100.x.x.4:80/api/collector/status \
  -H "X-Collector-Key: sua_chave"
```

### "Error: Connection refused"

```bash
# Collector está tentando conectar no IP errado
# Verificar em /opt/vnstat-collector/.env
cat /opt/vnstat-collector/.env

# Se IP está errado:
sudo nano /opt/vnstat-collector/.env
# Editar VNSTAT_API_URL
# Salvar + testar
/opt/vnstat-collector/run.sh
```

### "Mariadb permission denied"

```bash
# Credenciais erradas em DATABASE_URL
# Editar .env
nano .env

# Recriar banco
docker-compose down
rm -rf mariadb_data/
docker-compose up -d
```

---

## 📚 Próximos passos

1. **Setup completo:** Veja `DEPLOYMENT.md` para seu setup específico
2. **API docs:** Veja `API.md` para todos os endpoints
3. **Desenvolvimento:** Modificar `backend/routes/api.py` e `frontend/templates/`

---

## 🎓 Stack usado

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| **Frontend** | HTML5 + Chart.js | 4.4.0 |
| **Backend** | Flask + JWT | 3.0.0 |
| **Database** | MariaDB | 11.1 |
| **Container** | Docker | latest |
| **Web Server** | Nginx | alpine |
| **Auth** | JWT cookies | 4.5.3 |

Tudo com **máximas práticas**: tipo hints, docstrings, error handling, segurança.

---

## 🚨 Checklist de produção

- [ ] Mudar `ADMIN_PASS` no `.env`
- [ ] Mudar `COLLECTOR_API_KEY` (algo como `openssl rand -hex 32`)
- [ ] Mudar `SECRET_KEY` e `JWT_SECRET_KEY`
- [ ] Ativar HTTPS via Nginx Proxy Manager
- [ ] Backup diário do banco (MariaDB)
- [ ] Monitorar logs: `docker-compose logs -f`
- [ ] Limpar dados antigos periodicamente (SQL)

---

## 💬 Suporte

- **Dúvidas sobre setup:** Veja `DEPLOYMENT.md`
- **API reference:** Veja `API.md`
- **Bugs/features:** Abra issue no repo
- **Customização:** Modifique código — está bem comentado!

---

**Bom painel! 🎉**

Enjoy monitorando seu tráfego de rede com estilo. 

Se curtiu, dá uma ⭐ no repo!
