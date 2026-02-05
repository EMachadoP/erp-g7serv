from django.core.mail import EmailMessage
from django.template.loader import render_to_string
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
            # Substituição de Placeholders
            placeholders = {
                '{cliente}': client.name,
                '{valor}': f"R$ {invoice.amount}",
                '{vencimento}': invoice.due_date.strftime('%d/%m/%Y'),
                '{fatura}': invoice.number,
                '{link_boleto}': invoice.boleto_url or "Link não disponível",
                '{link_nf}': invoice.nfse_link or "Link não disponível",
            }
            
            subject = template.subject
            body = template.body
            for key, value in placeholders.items():
                subject = subject.replace(key, str(value or "-"))
                body = body.replace(key, str(value or "-"))
        else:
            # Fallback total (caso não existam templates no banco)
            competence = f"{invoice.competence_month:02d}/{invoice.competence_year}"
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
                # Fallback em HTML premium caso o template herde erro ou não exista
                body = f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #0046ad;">Olá {client.name},</h2>
                    <p style="font-size: 16px; color: #333;">Sua fatura de <strong>{competence}</strong> já está disponível.</p>
                    <div style="background: #f4f7ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Valor:</strong> R$ {invoice.amount}</p>
                        <p style="margin: 5px 0;"><strong>Vencimento:</strong> {invoice.due_date.strftime('%d/%m/%Y')}</p>
                    </div>
                    <p style="font-size: 14px; color: #666;">Você pode acessar os documentos pelos botões abaixo ou visualizar os arquivos em anexo.</p>
                    <div style="margin-top: 25px;">
                        <a href="{invoice.boleto_url or '#'}" style="background-color: #0046ad; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-right: 10px;">Abrir Boleto</a>
                        {f'<a href="{invoice.nfse_link}" style="background-color: #6c757d; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Ver Nota Fiscal</a>' if invoice.nfse_link else ''}
                    </div>
                    <p style="margin-top: 30px; font-size: 12px; color: #999; border-top: 1px solid #eee; pt: 10px;">Obrigado,<br><strong>G7Serv Administradora</strong></p>
                </div>
                """
        
        if getattr(settings, 'BREVO_API_KEY', None):
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
                        "name": f"Fatura_{invoice.number}.pdf"
                    })
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
                        "name": f"Boleto_{invoice.number}.pdf"
                    })
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
