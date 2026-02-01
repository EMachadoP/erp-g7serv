# Product Specification: ERP G7Serv

## Visão Geral
O ERP G7Serv é uma plataforma de gestão de Field Service e Operacional. 
URL de Produção: https://web-production-34bc.up.railway.app

## Módulos Principais para Teste:

### 1. Autenticação
- Endpoint: `/admin/`
- Objetivo: Acesso restrito para administradores e técnicos.

### 2. Comercial & CRM
- Funcionalidade: Cadastro de clientes (PF/PJ), geração de orçamentos e gestão de contratos.
- Regra de Negócio: Orçamentos aprovados devem permitir a geração de Ordens de Serviço.

### 3. Operacional (Field Service)
- Funcionalidade: Gestão de Ordens de Serviço (OS).
- Fluxo: Pendente -> Em Andamento -> Concluída.
- Requisito: Registro de geolocalização no Check-in/Check-out e preenchimento de checklists.

### 4. Financeiro
- Funcionalidade: Fluxo de caixa, contas a pagar/receber e conciliação bancária.

### 5. Inteligência Artificial (Studio AI)
- Funcionalidade: Triagem de mensagens e consulta de status via IA.
- Endpoint de Teste: `/ai/processar/`
