# ✅ DEPLOY CHECKLIST - ERP G7Serv

## 📋 PRÉ-DEPLOY

- [ ] DEBUG=False
- [ ] SECRET_KEY em variável de ambiente
- [ ] ALLOWED_HOSTS configurado
- [ ] Todos os testes passando
- [ ] Migrações aplicadas
- [ ] requirements.txt atualizado

## 🚀 DEPLOY

```bash
git push origin main
```

## ✅ PÓS-DEPLOY

- [ ] Aplicação online
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Módulos funcionam
- [ ] AI Core responde
- [ ] Segurança validada

## 🧪 TESTES MANUAIS

```bash
# Teste AI
curl -X POST https://web-production-34bc.up.railway.app/ai/processar/ \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "teste", "nome": "teste"}'
```
