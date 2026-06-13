# API Documentation — vnstat Dashboard

Documentação completa da API REST com exemplos cURL.

---

## 🔐 Autenticação

### POST `/api/auth/login`

Login com JWT (salvo em cookie).

**Request:**
```bash
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "changeme"
  }' \
  -c cookies.txt
```

**Response (200):**
```json
{
  "ok": true,
  "username": "admin"
}
```

Cookie `access_token_cookie` é automaticamente salvo e enviado em requisições subsequentes.

---

### GET `/api/auth/me`

Retorna usuário autenticado.

**Request:**
```bash
curl http://localhost/api/auth/me \
  -b cookies.txt
```

**Response (200):**
```json
{
  "id": 1,
  "username": "admin"
}
```

**Response (401):**
```json
{
  "error": "Token has expired"
}
```

---

### POST `/api/auth/logout`

Logout e limpa cookie.

**Request:**
```bash
curl -X POST http://localhost/api/auth/logout \
  -b cookies.txt
```

**Response (200):**
```json
{
  "ok": true
}
```

---

## 📊 Dados (requer JWT)

### GET `/api/overview`

Retorna agregado total, status de hosts, KPIs.

**Request:**
```bash
curl http://localhost/api/overview \
  -b cookies.txt
```

**Response (200):**
```json
{
  "total_rx": 125000000000,
  "total_tx": 98000000000,
  "total_combined": 223000000000,
  "total_rx_fmt": "125.0 GB",
  "total_tx_fmt": "98.0 GB",
  "total_combined_fmt": "223.0 GB",
  "live_rx_rate": 1048576,
  "live_tx_rate": 524288,
  "live_rx_fmt": "1.0 MB/s",
  "live_tx_fmt": "512.0 KB/s",
  "month_rx": 5000000000,
  "month_tx": 4000000000,
  "month_rx_fmt": "5.0 GB",
  "month_tx_fmt": "4.0 GB",
  "hosts": [
    {
      "id": 1,
      "name": "pi",
      "display_name": "Raspberry Pi",
      "tailscale_ip": "100.x.x.1",
      "interface": "eth0",
      "active": true,
      "last_seen": "2024-01-15T14:30:00",
      "online": true,
      "rx_total": 50000000000,
      "tx_total": 40000000000,
      "rx_total_fmt": "50.0 GB",
      "tx_total_fmt": "40.0 GB",
      "rx_rate": 524288,
      "tx_rate": 262144,
      "rx_rate_fmt": "512.0 KB/s",
      "tx_rate_fmt": "256.0 KB/s"
    },
    {
      "id": 2,
      "name": "note",
      "display_name": "Note (Debian)",
      "tailscale_ip": "100.x.x.2",
      "interface": "enp2s0",
      "active": true,
      "last_seen": "2024-01-15T14:25:00",
      "online": true,
      "rx_total": 40000000000,
      "tx_total": 30000000000,
      "rx_total_fmt": "40.0 GB",
      "tx_total_fmt": "30.0 GB",
      "rx_rate": 262144,
      "tx_rate": 131072,
      "rx_rate_fmt": "256.0 KB/s",
      "tx_rate_fmt": "128.0 KB/s"
    },
    {
      "id": 3,
      "name": "ser4ph-arm",
      "display_name": "Oracle ARM VPS",
      "tailscale_ip": "100.x.x.3",
      "interface": "eth0",
      "active": true,
      "last_seen": "2024-01-15T14:28:00",
      "online": true,
      "rx_total": 35000000000,
      "tx_total": 28000000000,
      "rx_total_fmt": "35.0 GB",
      "tx_total_fmt": "28.0 GB",
      "rx_rate": 262144,
      "tx_rate": 131072,
      "rx_rate_fmt": "256.0 KB/s",
      "tx_rate_fmt": "128.0 KB/s"
    }
  ],
  "host_count": 3,
  "online_count": 3
}
```

---

### GET `/api/hosts`

Lista todos os hosts ativos.

**Request:**
```bash
curl http://localhost/api/hosts \
  -b cookies.txt
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "pi",
    "display_name": "Raspberry Pi",
    "tailscale_ip": "100.x.x.1",
    "interface": "eth0",
    "active": true,
    "last_seen": "2024-01-15T14:30:00"
  },
  ...
]
```

---

### GET `/api/host/<name>`

Detalhe de um host específico com histórico.

**Request:**
```bash
curl http://localhost/api/host/pi \
  -b cookies.txt
```

**Response (200):**
```json
{
  "host": {
    "id": 1,
    "name": "pi",
    "display_name": "Raspberry Pi",
    "tailscale_ip": "100.x.x.1",
    "interface": "eth0",
    "active": true,
    "last_seen": "2024-01-15T14:30:00"
  },
  "timeline": [
    {
      "t": "2024-01-15T10:00:00",
      "rx": 1024000,
      "tx": 512000,
      "rx_rate": 262144,
      "tx_rate": 131072
    },
    ...
  ],
  "days": [
    {
      "date": "2024-01-15",
      "rx": 10000000000,
      "tx": 8000000000
    },
    ...
  ],
  "months": [
    {
      "label": "2024-01",
      "rx": 150000000000,
      "tx": 120000000000
    },
    ...
  ],
  "current": {
    "rx_total": 50000000000,
    "tx_total": 40000000000,
    "rx_rate": 524288,
    "tx_rate": 262144,
    "rx_total_fmt": "50.0 GB",
    "tx_total_fmt": "40.0 GB"
  }
}
```

---

### GET `/api/chart/daily`

Gráfico dos últimos 30 dias (ou custom).

**Request:**
```bash
# Últimos 30 dias
curl http://localhost/api/chart/daily \
  -b cookies.txt

# Últimos 60 dias
curl "http://localhost/api/chart/daily?days=60" \
  -b cookies.txt

# Apenas pi e note
curl "http://localhost/api/chart/daily?hosts=pi,note" \
  -b cookies.txt
```

**Response (200):**
```json
{
  "labels": [
    "2024-01-01",
    "2024-01-02",
    ...
  ],
  "datasets": [
    {
      "label": "Raspberry Pi ↓",
      "host": "pi",
      "type": "rx",
      "data": [10000000000, 11000000000, ...],
      "borderColor": "#38bdf8",
      "backgroundColor": "#38bdf822"
    },
    {
      "label": "Raspberry Pi ↑",
      "host": "pi",
      "type": "tx",
      "data": [8000000000, 9000000000, ...],
      "borderColor": "#f472b6",
      "backgroundColor": "#f472b622"
    },
    ...
  ]
}
```

---

### GET `/api/chart/monthly`

Gráfico dos últimos 12 meses.

**Request:**
```bash
curl http://localhost/api/chart/monthly \
  -b cookies.txt
```

**Response (200):**
```json
{
  "labels": [
    "2023-01",
    "2023-02",
    ...
    "2024-01"
  ],
  "datasets": [
    {
      "label": "Raspberry Pi",
      "rx": [150000000000, 160000000000, ...],
      "tx": [120000000000, 130000000000, ...],
      "color": "#38bdf8"
    },
    {
      "label": "Note (Debian)",
      "rx": [120000000000, 140000000000, ...],
      "tx": [100000000000, 110000000000, ...],
      "color": "#34d399"
    },
    ...
  ]
}
```

---

## 📡 Collector (sem autenticação JWT, mas com X-Collector-Key)

### POST `/api/collector/push`

Receiver para agents pushear dados vnstat.

**Request:**
```bash
curl -X POST http://localhost/api/collector/push \
  -H "Content-Type: application/json" \
  -H "X-Collector-Key: sua_chave_aqui" \
  -d '{
    "host": "pi",
    "interface": "eth0",
    "captured_at": "2024-01-15T14:30:00+00:00",
    "rx_total": 50000000000,
    "tx_total": 40000000000,
    "rx_hour": 1000000000,
    "tx_hour": 800000000,
    "rx_rate": 524288,
    "tx_rate": 262144,
    "days": [
      {
        "date": "2024-01-15",
        "rx": 10000000000,
        "tx": 8000000000
      },
      {
        "date": "2024-01-14",
        "rx": 9500000000,
        "tx": 7500000000
      }
    ],
    "months": [
      {
        "year": 2024,
        "month": 1,
        "rx": 150000000000,
        "tx": 120000000000
      }
    ]
  }'
```

**Response (200):**
```json
{
  "ok": true,
  "host": "pi"
}
```

**Response (401):**
```json
{
  "error": "Unauthorized"
}
```

**Response (400):**
```json
{
  "error": "No JSON body"
}
```

---

### GET `/api/collector/status`

Health check para collectors.

**Request:**
```bash
curl http://localhost/api/collector/status \
  -H "X-Collector-Key: sua_chave_aqui"
```

**Response (200):**
```json
{
  "ok": true,
  "ts": "2024-01-15T14:30:00+00:00"
}
```

---

## 📝 Exemplos em Python

### Login e fetch overview

```python
import requests
import json

BASE_URL = "http://localhost"
ADMIN_USER = "admin"
ADMIN_PASS = "changeme"

session = requests.Session()

# Login
res = session.post(f"{BASE_URL}/api/auth/login", json={
    "username": ADMIN_USER,
    "password": ADMIN_PASS,
})
print(f"Login: {res.status_code} {res.json()}")

# Get overview
res = session.get(f"{BASE_URL}/api/overview")
data = res.json()
print(json.dumps(data, indent=2))
```

### Collector push (agents)

```python
import requests
import subprocess
import json
from datetime import datetime, timezone

API_URL = "http://100.x.x.4:5000"
COLLECTOR_KEY = "sua_chave_aqui"
HOST_NAME = "pi"

# Get vnstat data
result = subprocess.run(["vnstat", "--json"], capture_output=True, text=True)
raw = json.loads(result.stdout)

# Extract interface
iface = raw["interfaces"][0]
traffic = iface.get("traffic", {})

# Build payload
payload = {
    "host": HOST_NAME,
    "interface": iface["name"],
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "rx_total": traffic.get("total", {}).get("rx", 0),
    "tx_total": traffic.get("total", {}).get("tx", 0),
    "rx_hour": traffic.get("hour", [{}])[-1].get("rx", 0),
    "tx_hour": traffic.get("hour", [{}])[-1].get("tx", 0),
    "rx_rate": iface.get("rxspeed", 0),
    "tx_rate": iface.get("txspeed", 0),
    "days": [
        {"date": f"{d['date']['year']}-{d['date']['month']:02d}-{d['date']['day']:02d}",
         "rx": d["rx"], "tx": d["tx"]}
        for d in traffic.get("day", [])
    ],
    "months": [
        {"year": m["date"]["year"], "month": m["date"]["month"],
         "rx": m["rx"], "tx": m["tx"]}
        for m in traffic.get("month", [])
    ],
}

# Push
res = requests.post(
    f"{API_URL}/api/collector/push",
    json=payload,
    headers={"X-Collector-Key": COLLECTOR_KEY},
)
print(f"{res.status_code} {res.json()}")
```

---

## ⏱️ Rate Limiting

Não há rate limiting implementado por padrão. Em produção, considere:

```bash
# Adicionar Flask-Limiter
pip install Flask-Limiter

# Usar em app factory:
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: get_jwt_identity())

@api.get("/overview")
@jwt_required()
@limiter.limit("30 per minute")
def overview(): ...
```

---

## 🔍 Troubleshooting

### 401 Unauthorized

```bash
# JWT expirado
# Fazer novo login

curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme"}' \
  -c new_cookies.txt

# Use a nova cookie
curl http://localhost/api/overview \
  -b new_cookies.txt
```

### 404 Not Found

```bash
# Host não existe
curl http://localhost/api/host/nonexistent \
  -b cookies.txt

# → {"error": "Not Found"}
```

### Collector push retorna 401

```bash
# X-Collector-Key inválida ou ausente
curl -X POST http://localhost/api/collector/push \
  -H "X-Collector-Key: chave_errada" \
  -d '{...}'

# Verificar COLLECTOR_API_KEY no .env
```

---

## 📚 Mais informações

- Veja `README.md` para guia geral
- Veja `DEPLOYMENT.md` para deploy no seu homelab
- Código da API: `backend/routes/api.py`, `backend/routes/collector.py`
