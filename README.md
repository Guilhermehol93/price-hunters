# Price Hunter 🎯

> **Sistema Inteligente de Radar de Ofertas, Histórico de Preços e Alertas Instantâneos no Telegram**  
> *Compatível com Supabase, PostgreSQL 16 e Implantação Automatizada via Portainer / Docker.*

---

## 📖 Documentação Completa (Manual Oficial)

O projeto inclui um documento HTML **100% autossuficiente, responsivo e em português brasileiro** com todos os detalhes de arquitetura, instalação, desenvolvimento, manutenção e segurança:

👉 **[Abrir o Manual Completo: `docs/manual-price-hunter.html`](file:///d:/Aplicacao/Busca%20de%20promoção/docs/manual-price-hunter.html)**

*(Basta abrir o arquivo diretamente em qualquer navegador moderno como Chrome, Firefox, Edge ou Safari — ele funciona de forma autônoma sem requisições a CDNs externas).*

---

## 🚀 Principais Destaques

- **Radar de Oportunidades com IA:** Algoritmo ponderado de *Opportunity Score* (0 a 100) que analisa desvios em relação à média de 30/60/90 dias, proximidade da mínima histórica e penaliza descontos maquiados ("metade do dobro").
- **Compatibilidade Dual de Persistência:**
  - **Modalidade A:** PostgreSQL Local em container Docker (100% self-hosted).
  - **Modalidade B:** Supabase Gerenciado com Transaction Pooler (porta 6543) e Row Level Security (RLS) nativo.
- **Cadastro Universal por URL:** Rastreie qualquer produto informando o link, com blindagem ativa contra ataques de **SSRF (Server-Side Request Forgery)**.
- **Alertas no Telegram:** Disparo instantâneo com foto, preço anterior, preço atual, percentual real de desconto e proteção contra spam (cooldown).
- **Pronto para Portainer & Umbrel:** Arquivos `docker-compose.yml` otimizados com limites de recursos, healthchecks e volumes persistentes.

---

## ⚡ Início Rápido

### 1. Configuração de Variáveis de Ambiente
Copie o template de exemplo:
```bash
cp .env.example .env
```
Edite o arquivo `.env` para definir se utilizará o PostgreSQL local ou as credenciais do seu projeto Supabase, além do Token do Telegram.

### 2. Implantação via Docker Compose
Para subir o ambiente completo com PostgreSQL local:
```bash
docker compose -f docker-compose.local.yml up -d --build
```
Ou para conectar diretamente ao Supabase externo:
```bash
docker compose -f docker-compose.supabase.yml up -d --build
```

### 3. Acessar a Interface
Abra no seu navegador:
- **Interface Web:** `http://localhost:18080`
- **Documentação Interativa da API (Swagger):** `http://localhost:8000/docs`

---

## 🧪 Suíte de Testes Automatizados

O projeto conta com testes unitários e de integração cobrindo inteligência estatística, segurança anti-SSRF, regras de alerta e endpoints REST:

```bash
pytest tests/ -v
```

---

## 📁 Estrutura do Projeto

Consulte a **Seção 2** do manual [`docs/manual-price-hunter.html`](file:///d:/Aplicacao/Busca%20de%20promoção/docs/manual-price-hunter.html) para o detalhamento da arquitetura técnica e organização dos módulos.
