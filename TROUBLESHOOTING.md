# 🔧 TROUBLESHOOTING - ERP G7Serv

## Erros Comuns

### DisallowedHost
```python
ALLOWED_HOSTS = ['.railway.app', 'seu-dominio.railway.app']
```

### CSRF Verification Failed
Certifique-se de que `CSRF_TRUSTED_ORIGINS` inclua o domínio do Railway com `https://`.

### Static Files Not Loading
Rode `python manage.py collectstatic --noinput` e verifique se o `WhiteNoise` está no `MIDDLEWARE`.

### Static Files 404
```bash
python manage.py collectstatic --noinput
```

### Migrações Pendentes
```bash
railway run python manage.py migrate
```

## Comandos Úteis

### Logs
```bash
railway logs
```

### Shell
```bash
railway run python manage.py shell
```

### Check Deploy
```bash
python manage.py check --deploy
```
