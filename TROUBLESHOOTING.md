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
