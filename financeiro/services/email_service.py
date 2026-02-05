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
            body = render_to_string('emails/fatura_corpo.html', context)
        
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
                logger.warning(f"Não foi possível anexar o arquivo PDF: {e}")
            
        try:
            email.send()
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail de faturamento para {recipient_email}: {e}")
            return False
