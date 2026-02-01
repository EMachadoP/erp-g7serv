# ERP G7Serv - Gestão Inteligente Studio AI

Sistema ERP modular para gestão comercial, operacional e financeira com triagem automatizada via Inteligência Artificial.

## 🛠️ Stack Tecnológica
- **Backend**: Python 3.13 / Django 5.1.5
- **Banco de Dados**: PostgreSQL 16 (Railway)
- **Frontend**: Bootstrap 5 / HTMX / Chart.js
- **Segurança**: WhiteNoise (Static Files) / SSL Hardening / HSTS
- **Infra**: Docker / Railway

## 🚀 URLs de Acesso Rápido
| Módulo | Endpoint | Descrição |
| :--- | :--- | :--- |
| **Admin** | `/admin/` | Gestão administrativa do sistema |
| **Dashboard** | `/dashboard/` | Painel BI com indicadores e gráficos |
| **Clientes** | `/comercial/clientes/` | Gestão da base de clientes |
| **Orçamentos** | `/comercial/orcamentos/` | Criação e acompanhamento comercial |
| **Operacional** | `/operacional/os/` | Ordens de Serviço e Checklist |
| **Financeiro** | `/financeiro/contas-a-pagar/` | Fluxo de caixa e obrigações |
| **AI Triage** | `/ai/processar/` | Endpoint de integração para triagem |

## ⚙️ Instalação Local
1. Clone o repositório.
2. Crie e ative um ambiente virtual (`.venv`).
3. Instale as dependências: `pip install -r requirements.txt`.
4. Configure o `.env` (use `.env.example` como base).
5. Execute as migrações: `python manage.py migrate`.
6. Rode o servidor: `python manage.py runserver`.

## 🧪 Testes de Integração
Para garantir a estabilidade dos módulos críticos, execute:
```bash
python manage.py test erp.tests_integration
```

## ☁️ Deploy via Railway
O deploy é automático ao realizar push para a branch `main`.
Consulte o arquivo `DEPLOY_CHECKLIST.md` para mais detalhes.
