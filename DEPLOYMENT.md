# Deployment Guide — vnstat Dashboard no seu Homelab

Este guia é específico para seu setup com **Oracle ARM VPS**, **Raspberry Pi**, **Note (Debian 12)** e **Ryzen (Windows)**.

---

## 📍 Onde rodar

**Recomendação: Oracle ARM VPS (ser4ph-arm)** — já tem MariaDB, Nginx Proxy Manager, está sempre ligado.

```bash
# No Oracle ARM
cd /opt
git clone <seu-repo> vnstat-dashboard
cd vnstat-dashboard
```

---

## 🔗 Configuração de Rede (Tailscale)

Os collectors (em cada host) vão pushear para o servidor central via Tailscale.

**Descubra os IPs Tailscale:**
```bash
# Em cada host
tailscale ip

# Exemplo output:
# 100.x.x.1 (pi)
# 100.x.x.2 (note)
# 100.x.x.3 (ryzen)
# 100.x.x.4 (ser4ph-arm — o servidor)
```

**No `.env` do Oracle ARM, configure:**
```bash
HOSTS=pi:Raspberry Pi:100.x.x.1,note:Note (Debian):100.x.x.2,ryzen:Ryzen (Windows):100.x.x.3,ser4ph-arm:Oracle ARM:100.x.x.4
```

---

## 🐳 Deploy com Docker (recomendado)

### 1. Clone e configure

```bash
ssh ubuntu@seu_oracle_ip

cd /opt
git clone <seu-repo> vnstat-dashboard
cd vnstat-dashboard

# Criar .env seguro
cp .env.example .env
nano .env
# Editar HOSTS com os IPs Tailscale descobertos
# Editar COLLECTOR_API_KEY — algo como: $(openssl rand -hex 24)
```

### 2. Build e start

```bash
docker-compose up -d

# Verificar logs
docker-compose logs -f app
```

Quando ver:
```
[2024-...] INFO in app: Serving Flask app...
```

✓ Pronto!

### 3. Expor via Nginx Proxy Manager (seu setup já usa)

**No Nginx Proxy Manager (`npm.nemik.top`):**
1. Novo "Proxy Host"
2. Domain: `vnstat.nemik.top` (ou seu domínio)
3. Scheme: `http`, Forward hostname: `container_ip:80` (interno da rede Docker)
4. SSL: Cloudflare/Let's Encrypt
5. WebSocket: ligado
6. Forward auth: desabilitado (JWT próprio basta)

Acessar: https://vnstat.nemik.top

---

## 📡 Instalar coletores (em cada host)

### Pi (Raspberry Pi)

```bash
ssh pi@100.x.x.1

cd /tmp
git clone <seu-repo> vnstat-dashboard-collector
cd vnstat-dashboard-collector/collector

# Obter a COLLECTOR_API_KEY do .env do Oracle
COLLECTOR_KEY="seu_collector_key_aqui"

sudo bash install-collector.sh \
  pi \
  "http://100.x.x.4" \
  "$COLLECTOR_KEY" \
  "eth0"

# Testar
/opt/vnstat-collector/run.sh
# → [2024-...] Pushed OK — {"ok": true, "host": "pi"}

# Verificar cron
crontab -l | grep vnstat

# Logs
tail /var/log/vnstat-collector.log
```

### Note (Debian 12 laptop)

```bash
ssh rodri@100.x.x.2

cd /tmp
git clone <seu-repo> vnstat-dashboard-collector
cd vnstat-dashboard-collector/collector

COLLECTOR_KEY="seu_collector_key_aqui"

sudo bash install-collector.sh \
  note \
  "http://100.x.x.4" \
  "$COLLECTOR_KEY" \
  "enp2s0"  # Ajustar para sua interface real

# Test + cron
/opt/vnstat-collector/run.sh
crontab -l | grep vnstat
```

### Ryzen (Windows 10)

Windows **não tem vnstat nativamente**. Opções:

#### Opção A: WSL2 + Linux nativo

```powershell
# Em PowerShell (admin)
wsl --install Ubuntu-22.04
wsl
# Dentro do WSL:
```

```bash
sudo apt-get install vnstat
cd /tmp
git clone <seu-repo> vnstat-dashboard-collector
cd vnstat-dashboard-collector/collector

COLLECTOR_KEY="seu_collector_key_aqui"

bash install-collector.sh \
  ryzen \
  "http://100.x.x.4" \
  "$COLLECTOR_KEY" \
  "eth0"  # Interface do WSL (adaptar)

crontab -e
# Adicionar linha (já deve estar):
# */5 * * * * /opt/vnstat-collector/run.sh
```

#### Opção B: PowerShell + script nativo (avançado)

Se quiser usar Windows nativo, converter `collector.py` para PowerShell — não incluso neste guia, mas é viável.

---

## ✅ Verificar status

### Dashboard está rodando?

```bash
# No Oracle ARM
docker-compose ps

# Deve mostrar:
# vnstat-db    ... Up
# vnstat-app   ... Up  
# vnstat-web   ... Up
```

### Colectores estão enviando?

```bash
# Acessar login
curl -X POST https://vnstat.nemik.top/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua_senha"}'

# Deve retornar cookie com JWT

# Agora query os dados
curl https://vnstat.nemik.top/api/overview \
  --cookie "access_token_cookie=..."

# Deve retornar JSON com hosts e métricas
```

### Logs detalhados

```bash
# Flask
docker-compose logs app

# MariaDB
docker-compose logs db

# Nginx
docker-compose logs web

# Em tempo real
docker-compose logs -f
```

---

## 🔄 Integração com seu setup existente

### Portainer
Já pode adicionar a stack manualmente no Portainer:
```bash
# Copiar docker-compose.yml para Portainer
# Ou usar `docker-compose up -d` direto
```

### Cloudflare
Já usa via Nginx Proxy Manager — tudo compatível.

### Let's Encrypt / SSL
O Nginx Proxy Manager já cuida via Cloudflare — sem fazer nada extra.

### Tailscale
Já integrado — collectors pushear via Tailscale, sem precisar expor a API internamente.

---

## 🎯 URLs finais

- **Dashboard:** https://vnstat.nemik.top
- **Login padrão:**
  - User: `admin`
  - Pass: (conforme configurado no `.env`)

---

## 📊 Dados esperados

Após ~15 minutos com coletores rodando:

```
Dashboard → Agregado Total:
  • Total Recebido: (RX cumulative de todos hosts)
  • Total Enviado: (TX cumulative)
  • Total Mês: dados do mês atual
  • Taxa ao Vivo: atualiza a cada 30s

Hosts:
  • 3 cards (pi, note, ser4ph-arm)
  • Status online/offline (depende de cron)
  • RX/TX totais por host

Gráficos:
  • Últimos 30 dias (barras)
  • Últimos 12 meses (linhas)
```

---

## 🔐 Pós-deploy: segurança

1. **Mudar senha admin:**
   ```bash
   # Via SQL
   docker-compose exec db mariadb -u root -p vnstat_dash
   > SELECT * FROM users;
   > UPDATE users SET password_hash='...' WHERE username='admin';
   ```
   Ou usar interface de login.

2. **Backup do banco:**
   ```bash
   docker-compose exec db mysqldump -u vnstat -p vnstat_dash > backup.sql
   ```

3. **Limpar logs antigos:**
   ```bash
   docker-compose exec db mysql -u vnstat -p vnstat_dash -e \
     "DELETE FROM traffic_snapshots WHERE captured_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);"
   ```

---

## 🐛 Troubleshooting

### Colector não conecta (erro "Connection refused")

```bash
# No host collector
# 1. Verifica conectividade Tailscale
ping 100.x.x.4

# 2. Test TCP direto
nc -zv 100.x.x.4 80

# 3. Testar curl
curl http://100.x.x.4:5000/api/collector/status \
  -H "X-Collector-Key: CHAVE_AQUI"

# 4. Verificar logs Flask
ssh ubuntu@oracle_ip
docker-compose logs app | grep ERROR
```

### Dashboard sem dados após 30 min

```bash
# No Oracle
# 1. Verificar se dados chegam no banco
docker-compose exec db mariadb -u vnstat -p vnstat_dash
> SELECT COUNT(*) FROM traffic_snapshots;

# Se = 0, coletores não estão conectando.

# 2. Testar collector manualmente
ssh pi@100.x.x.1
/opt/vnstat-collector/run.sh

# Deve retornar: [2024-...] Pushed OK

# 3. Se erro, verificar variáveis
cat /opt/vnstat-collector/.env
```

### Mariadb permission denied

```bash
# Refazer credenciais
docker-compose down
rm -rf mariadb_data/
docker-compose up -d db
# Aguarda inicializar
docker-compose up -d
```

---

## 📈 Performance & Scaling

**Limite atual:**
- 3 hosts
- 5 min intervalo = 288 pontos/dia/host
- 1 ano ≈ 315KB/host em snapshots

**Se crescer:**
- Aumentar intervalo (ex: 10 min)
- Mover MariaDB para volume separado (NFS)
- Agregar dados antigos (arquivar daily/monthly)

---

## 🎓 Aprender mais

- **vnstat docs:** https://humdi.net/vnstat/
- **Chart.js:** https://www.chartjs.org/docs/latest/
- **Flask:** https://flask.palletsprojects.com/
- **MariaDB:** https://mariadb.com/kb/

---

**Bom deploy! 🚀**

Qualquer dúvida, abra issue no repo.
