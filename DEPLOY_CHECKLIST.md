# Checklist de Deploy - ERP G7Serv

Siga este checklist para garantir deploys seguros no ambiente Railway.

## 1. Pré-Deploy (Local)
- [ ] Rodar testes: `python manage.py test erp.tests_integration`
- [ ] Verificar `settings.py`: Garantir que `DEBUG` use `config('DEBUG')` e headers de segurança estejam ativos.
- [ ] Validar migrations: `python manage.py makemigrations`.
- [ ] Commitar mudanças: `git commit -m "feat/fix: descrição"`

## 2. Configurações Railway (Dash)
- [ ] Variáveis obrigatórias:
  - `SECRET_KEY`
  - `DATABASE_URL`
  - `ALLOWED_HOSTS`
  - `CSRF_TRUSTED_ORIGINS`
- [ ] Variáveis opcionais:
  - `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (Para auto-criação).

## 3. Deploy
- [ ] Push para produção: `git push origin main`.
- [ ] Monitorar logs de build no Railway: `https://railway.app/project/.../service/...`.
- [ ] Verificar logs de execução (Deploy > Logs).

## 4. Pós-Deploy e Validação
- [ ] Acessar `/admin/` e validar login.
- [ ] Acessar `/dashboard/` e verificar se os gráficos carregam.
- [ ] Testar triagem AI: Enviar POST JSON para `/ai/processar/` e conferir retorno do protocolo.
- [ ] Rodar auditoria básica: `python manage.py check --deploy`.

## 5. Rollback (Se necessário)
- Reverter commit problemático: `git revert <hash>`.
- Push para GitHub.
- Verificar status do banco de dados (se houve migração destrutiva).
