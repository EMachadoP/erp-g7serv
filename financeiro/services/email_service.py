from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class BillingEmailService:
    @staticmethod
    def send_invoice_email(invoice):
        """
        Envia e-mail de fatura para o cliente com anexos (PDF Fatura, Boleto, etc).
        """
        competence = f"{invoice.competence_month:02d}/{invoice.competence_year}"
        client_name = invoice.client.name
        recipient_email = invoice.client.email
        
        if not recipient_email:
            logger.error(f"Erro ao enviar e-mail: Cliente {client_name} não possui e-mail cadastrado.")
            return False

        subject = f"Fatura Disponível - {client_name} - Ref. {competence}"
        
        # Renderizar corpo do e-mail
        context = {
            'invoice': invoice,
            'client_name': client_name,
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
