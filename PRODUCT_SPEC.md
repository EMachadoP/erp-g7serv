# Product Specification: ERP G7Serv (Refined)

## Módulos e Endpoints Reais:
1. **Autenticação**: `/admin/` (Login obrigatório)
2. **Comercial**: `/comercial/clientes/` e `/comercial/orcamentos/`
3. **Operacional**: `/operacional/os/` (Gestão de Ordens de Serviço)
4. **Financeiro**: `/financeiro/financeiro/` (Anteriormente root, agora caminhos específicos como /financeiro/contas-a-pagar/)
5. **Studio AI**: `/ai/processar/` (Método POST para triagem)

> [!NOTE]
> O módulo financeiro requer login. O TestSprite deve considerar o redirecionamento para o login ao acessar áreas protegidas.
