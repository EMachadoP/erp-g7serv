# 🏢 ERP G7Serv

Sistema de Gestão Empresarial completo desenvolvido em Django.

[![Django](https://img.shields.io/badge/Django-5.1.5-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Railway](https://img.shields.io/badge/Deploy-Railway-purple.svg)](https://railway.app/)

---

## 📋 Módulos do Sistema

| Módulo | Descrição | Status |
|--------|-----------|--------|
| 🔐 Auth | Autenticação e permissões | ✅ Funcional |
| 📊 Dashboard | BI Dashboard com métricas | ✅ Funcional |
| 💼 Comercial | Clientes, Orçamentos, Contratos | ✅ Funcional |
| 🔧 Operacional | Ordens de Serviço (OS) | ✅ Funcional |
| 💰 Financeiro | Contas a Pagar/Receber | ✅ Funcional |
| 🤖 AI Core | Triagem e Protocolo de Atendimento | ✅ Funcional |

---

## 🚀 URLs de Acesso

### Produção (Railway)
- **Dashboard:** https://web-production-34bc.up.railway.app/dashboard/
- **Admin:** https://web-production-34bc.up.railway.app/admin/
- **Comercial:** https://web-production-34bc.up.railway.app/comercial/clientes/
- **Operacional:** https://web-production-34bc.up.railway.app/operacional/os/
- **Financeiro:** https://web-production-34bc.up.railway.app/financeiro/contas-a-pagar/
- **AI API:** https://web-production-34bc.up.railway.app/ai/processar/

### Local
- **Dashboard:** http://localhost:8000/dashboard/
- **Admin:** http://localhost:8000/admin/

---

## 🛠️ Stack Tecnológica

### Backend
- Python 3.13
- Django 5.1.5
- PostgreSQL 16
- WhiteNoise (static files)
- django-htmx
- crispy-forms

### Frontend
- Bootstrap 5
- HTMX
- Font Awesome

### DevOps
- Railway (deploy)
- GitHub (versionamento)

---

## 💻 Instalação Local

```bash
# 1. Clone
git clone <url-do-repositorio>
cd erp-g7serv

# 2. Ambiente virtual
python -m venv venv
source venv/bin/activate

# 3. Dependências
pip install -r requirements.txt

# 4. Migrações
python manage.py migrate

# 5. Superusuário
python manage.py createsuperuser

# 6. Estáticos
python manage.py collectstatic --noinput

# 7. Rode
python manage.py runserver
```
