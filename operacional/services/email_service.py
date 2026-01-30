from django.core.mail import EmailMessage
from django.conf import settings
from .pdf_service import generate_preventive_pdf_bytes, get_checklist_filename
import io

def send_checklist_email(order, categories, responses):
    """
    Generates the checklist PDF and sends it to the client's email.
    """
    if not order.client.email:
        return False, "Cliente não possui e-mail cadastrado."
    
    # Generate PDF bytes
    pdf_content = generate_preventive_pdf_bytes(order, categories, responses)
    if not pdf_content:
        return False, "Erro ao gerar o PDF para anexo."
    
    filename = get_checklist_filename(order)
    subject = f"Relatório de Manutenção Preventiva - OS #{order.id} - {order.client.name}"
    body = f"""
Olá,

Segue em anexo o relatório detalhado da manutenção preventiva realizada em {order.checkout_time.strftime('%d/%m/%Y %H:%M')}.

Este relatório contém o checklist completo de todos os itens verificados, fotos das irregularidades encontradas e a assinatura do responsável.

Atenciosamente,
Equipe G7 Serv
    """
    
    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [order.client.email],
    )
    
    email.attach(filename, pdf_content, "application/pdf")
    
    try:
        email.send()
        return True, "E-mail enviado com sucesso!"
    except Exception as e:
        return False, f"Falha ao enviar e-mail: {str(e)}"
