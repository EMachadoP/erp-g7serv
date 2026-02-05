from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.safestring import mark_safe
from django.template.defaultfilters import linebreaksbr
from django.conf import settings
from core.models import EmailTemplate
import logging

logger = logging.getLogger(__name__)

class BillingEmailService:
    @staticmethod
    def send_invoice_email(invoice, template_id=None, connection=None):
        """
        Envia e-mail de fatura para o cliente com anexos (PDF Fatura, Boleto, etc).
        """
        client = invoice.client
        recipient_email = client.email
        
        if not recipient_email:
            logger.error(f"Erro ao enviar e-mail: {client.name} não possui e-mail cadastrado.")
            return False

        # 1. Obter Template (ou usar o padrão se não especificado)
        template = None
        if template_id:
            try:
                template = EmailTemplate.objects.get(id=template_id)
            except EmailTemplate.DoesNotExist:
                pass
        
        if not template:
            # Fallback para template padrão de boleto
            template = EmailTemplate.objects.filter(template_type='BOLETO_NF').first()

        if template:
            # Mês/Ano de Competência com fallback para data de emissão
            c_month = invoice.competence_month or invoice.issue_date.month
            c_year = invoice.competence_year or invoice.issue_date.year
            competence = f"{c_month:02d}/{c_year}"
            context_dict = {
                'cliente': client.name,
                'valor': f"R$ {invoice.amount}",
                'vencimento': invoice.due_date.strftime('%d/%m/%Y'),
                'fatura': invoice.number,
                'link_boleto': invoice.boleto_url or "#",
                'link_nf': invoice.nfse_link or "#",
                'competence': competence,
                'invoice': invoice,
            }

            # 1. Renderizar Assunto
            try:
                # Pré-processar tags do usuário {tag} para {{tag}}
                subject_text = template.subject
                for placeholder in ['cliente', 'valor', 'vencimento', 'fatura', 'link_boleto', 'link_nf', 'competence']:
                    subject_text = subject_text.replace(f'{{{placeholder}}}', f'{{{{{placeholder}}}}}')
                
                subject_template = Template(subject_text)
                subject = subject_template.render(Context(context_dict))
            except Exception as e:
                logger.error(f"Erro ao renderizar assunto do template: {e}")
                # Fallback manual para o assunto se o Template falhar
                subject = template.subject
                for k, v in context_dict.items():
                    subject = subject.replace(f'{{{k}}}', str(v))

            # 2. Renderizar Corpo do Usuário (aplicando linebreaksbr)
            try:
                # Pré-processar tags do usuário {tag} para {{tag}}
                body_content = template.body.replace('{', '{{').replace('}', '}}')
                
                # Remover tags redundantes se o usuário as deixou no template
                # Conforme solicitado: {cliente}, {vencimento}, {valor}, {link_boleto}, {fatura}
                tags_to_strip = ['{{cliente}}', '{{vencimento}}', '{{valor}}', '{{link_boleto}}', '{{fatura}}', '{{link_nf}}']
                for tag in tags_to_strip:
                    body_content = body_content.replace(tag, '')

                body_template = Template(body_content)
                user_body_html = body_template.render(Context(context_dict))
                
                # Remover assinaturas redundantes que o usuário pode ter deixado
                # Limpa termos comuns de encerramento se aparecerem no final
                redundant_terms = [
                    'obrigado', 'atenciosamente', 'equipe g7 serv', 'g7 serv', 
                    '81 3019-5654', 'att,', 'grato'
                ]
                
                # Limpeza agressiva de quebras de linha no final para tirar o "espaço extra"
                user_body_html = user_body_html.strip()
                
                # Tentar remover as últimas linhas se forem apenas assinatura
                lines = user_body_html.split('\n')
                cleaned_lines = []
                for line in lines:
                    line_lower = line.lower().strip()
                    if not any(term in line_lower for term in redundant_terms) or len(line_lower) > 50:
                        cleaned_lines.append(line)
                
                user_body_html = '\n'.join(cleaned_lines).strip()

                # Converter quebras de linha em <br> se não houver tags HTML detectadas
                if '<p' not in user_body_html.lower() and '<br' not in user_body_html.lower():
                    user_body_html = linebreaksbr(user_body_html)
            except Exception as e:
                logger.error(f"Erro ao renderizar corpo do template: {e}")
                user_body_html = linebreaksbr(template.body)

            # 3. Envolver no Layout Premium
            body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ width: 100%; max-width: 600px; margin: 20px auto; border: 1px solid #e0e6ed; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
                    .header {{ background-color: #0046ad; color: white; padding: 30px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .content {{ padding: 30px; background-color: #ffffff; }}
                    .details {{ background: #f8fbff; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #eef2f8; }}
                    .btn-container {{ text-align: center; margin: 30px 0; }}
                    .btn {{ display: inline-block; padding: 14px 30px; background-color: #0046ad; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; border: none; }}
                    .footer {{ font-size: 12px; color: #94a3b8; text-align: center; padding: 20px; background-color: #f1f5f9; }}
                    a {{ color: #0046ad; text-decoration: none; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header"><h1>G7 Serv</h1></div>
                    <div class="content">
                        {user_body_html}
                        
                        <div class="details">
                            <p><strong>Resumo do Faturamento:</strong></p>
                            <p>Valor: R$ {invoice.amount}<br>
                            Vencimento: {invoice.due_date.strftime('%d/%m/%Y')}<br>
                            Fatura: {invoice.number}</p>
                        </div>

                        <div class="btn-container">
                            <a href="{invoice.boleto_url or '#'}" class="btn">Visualizar Boleto / PIX</a>
                        </div>
                        
                        <p style="margin-top: 40px; border-top: 1px solid #f1f5f9; padding-top: 20px; font-size: 14px;">
                            Atenciosamente,<br><strong>Equipe G7 Serv</strong><br>
                            <span style="font-size: 12px; color: #94a3b8;">Suporte: 81 3019-5654</span>
                        </p>
                    </div>
                    <div class="footer"><p>Este é um e-mail automático enviado por G7 Serv.</p></div>
                </div>
            </body>
            </html>
            """
        else:
            # Fallback total (caso não existam templates no banco ou erro grave)
            c_month = invoice.competence_month or invoice.issue_date.month
            c_year = invoice.competence_year or invoice.issue_date.year
            competence = f"{c_month:02d}/{c_year}"
            subject = f"Fatura Disponível - {client.name} - Ref. {competence}"
            context = {
                'invoice': invoice,
                'client_name': client.name,
                'competence': competence,
                'due_date': invoice.due_date.strftime('%d/%m/%Y'),
                'amount': invoice.amount,
                'boleto_url': invoice.boleto_url,
                'nfse_link': invoice.nfse_link,
            }
            try:
                body = render_to_string('emails/fatura_corpo.html', context)
            except:
                # Fallback em HTML premium rígido
                logger.info(f"Usando fallback HTML premium para fatura {invoice.number}")
                body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                        .container {{ width: 100%; max-width: 600px; margin: 20px auto; border: 1px solid #e0e6ed; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
                        .header {{ background-color: #0046ad; color: white; padding: 30px 20px; text-align: center; }}
                        .header h1 {{ margin: 0; font-size: 24px; }}
                        .content {{ padding: 30px; background-color: #ffffff; }}
                        .details {{ background: #f8fbff; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #eef2f8; }}
                        .btn-container {{ text-align: center; margin: 30px 0; }}
                        .btn {{ display: inline-block; padding: 14px 30px; background-color: #0046ad; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px; }}
                        .footer {{ font-size: 12px; color: #94a3b8; text-align: center; padding: 20px; background-color: #f1f5f9; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header"><h1>FATURA DISPONÍVEL</h1></div>
                        <div class="content">
                            <p style="font-size: 18px;">Olá, <strong>{client.name}</strong>,</p>
                            <p>Informamos que a sua fatura referente ao serviço de <strong>{competence}</strong> já está disponível.</p>
                            <div class="details">
                                <p><strong>Valor Total:</strong> R$ {invoice.amount}</p>
                                <p><strong>Data de Vencimento:</strong> {invoice.due_date.strftime('%d/%m/%Y')}</p>
                                <p><strong>Número da Fatura:</strong> {invoice.number}</p>
                            </div>
                            <div class="btn-container">
                                <a href="{invoice.boleto_url or '#'}" class="btn">Visualizar Boleto</a>
                            </div>
                            <p style="font-size: 14px;">Em anexo a este e-mail, você também encontrará:</p>
                            <ul style="font-size: 14px; color: #64748b;">
                                <li>O boleto bancário para pagamento</li>
                                <li>O demonstrativo detalhado da fatura (PDF)</li>
                            </ul>
                            <p style="margin-top: 40px; border-top: 1px solid #f1f5f9; padding-top: 20px;">
                                Atenciosamente,<br><strong>G7Serv Administradora</strong><br>
                                <span style="font-size: 12px; color: #94a3b8;">Suporte: 81 3019-5654</span>
                            </p>
                        </div>
                        <div class="footer"><p>Este é um e-mail automático. Por favor, não responda.</p></div>
                    </div>
                </body>
                </html>
                """
        
        if getattr(settings, 'BREVO_API_KEY', None):
            # Garante que o PDF da Fatura existe ou é atualizado antes de enviar
            from faturamento.services.invoice_service import generate_invoice_pdf_file
            
            # Se não existe ou for solicitado, gera/regenera para garantir dados frescos
            logger.info(f"Garantindo PDF da fatura para {invoice.number}")
            generate_invoice_pdf_file(invoice)
            
            # Recarregar do banco para garantir que o campo pdf_fatura está atualizado no objeto
            invoice.refresh_from_db()

            return BillingEmailService.send_via_brevo(
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                invoice=invoice
            )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
            connection=connection
        )
        email.content_subtype = "html"
        
        # Anexar PDF da Fatura se existir e estiver acessível localmente
        if invoice.pdf_fatura:
            try:
                email.attach_file(invoice.pdf_fatura.path)
            except Exception as e:
                logger.warning(f"Não foi possível anexar o arquivo PDF local: {e}")
            
        try:
            email.send()
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail de faturamento via SMTP para {recipient_email}: {e}")
            return False

    @staticmethod
    def send_via_brevo(recipient_email, subject, body, invoice):
        """
        Envia e-mail via API HTTP da Brevo (Sendinblue).
        """
        import requests
        import base64
        import os
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        sender_email = settings.DEFAULT_FROM_EMAIL or "g7serv@g7serv.com.br"
        
        data = {
            "sender": {"email": sender_email, "name": "G7Serv"},
            "to": [{"email": recipient_email}],
            "subject": subject,
            "htmlContent": body,
            "attachment": []
        }
        
        # 1. Anexo: PDF da Fatura (Local)
        if invoice.pdf_fatura:
            try:
                with open(invoice.pdf_fatura.path, "rb") as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                    data["attachment"].append({
                        "content": content,
                        "name": f"Demonstrativo_Fatura_{invoice.number}.pdf"
                    })
                    logger.info(f"Anexando fatura detalhada: Demonstrativo_Fatura_{invoice.number}.pdf")
            except Exception as e:
                logger.warning(f"Falha ao carregar fatura local para Brevo: {e}")

        # 2. Anexo: Boleto (URL Remota)
        if invoice.boleto_url:
            try:
                resp = requests.get(invoice.boleto_url, timeout=10)
                if resp.status_code == 200:
                    content = base64.b64encode(resp.content).decode('utf-8')
                    data["attachment"].append({
                        "content": content,
                        "name": f"Boleto_Bancario_{invoice.number}.pdf"
                    })
                    logger.info(f"Anexando boleto da Cora: Boleto_Bancario_{invoice.number}.pdf")
            except Exception as e:
                logger.warning(f"Falha ao baixar boleto remoto para Brevo: {e}")

        try:
            response = requests.post(url, json=data, headers=headers, timeout=20)
            if response.status_code in [200, 201]:
                logger.info(f"E-mail enviado via Brevo para {recipient_email}")
                return True
            else:
                logger.error(f"Erro Brevo ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao conectar com Brevo: {e}")
            return False
