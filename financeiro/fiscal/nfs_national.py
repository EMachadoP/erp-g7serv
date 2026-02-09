from lxml import etree
from datetime import datetime
from signxml import XMLSigner
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
import base64
from django.db import transaction
from financeiro.models import EmpresaFiscal, NotaFiscalServico

class DPSGenerator:
    def __init__(self, empresa, nota, servico_detalhes):
        """
        empresa: EmpresaFiscal instance
        nota: NotaFiscalServico instance
        servico_detalhes: dict with 'codigo_cnae' and other required fields
        """
        self.empresa = empresa
        self.nota = nota
        self.servico = servico_detalhes

    def gerar_xml_bruto(self):
        # Namespace do Padrão Nacional
        ns = "http://www.sped.fazenda.gov.br/nfse"
        
        # O Padrão Nacional costuma usar o prefixo nfse para o namespace
        attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
        nsmap = {None: ns}
        
        dps = etree.Element("DPS", nsmap=nsmap, versao="1.01")
        inf_dps = etree.SubElement(dps, "infDPS", Id=f"DPS{self.nota.numero_dps}")
        
        # Ordem Rígida conforme Anexo I
        etree.SubElement(inf_dps, "tpAmb").text = "2" # 1-Prod, 2-Homologação
        etree.SubElement(inf_dps, "dhEmi").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        etree.SubElement(inf_dps, "verAplic").text = "G7Serv_v1"
        etree.SubElement(inf_dps, "serie").text = self.nota.serie
        etree.SubElement(inf_dps, "nDPS").text = str(self.nota.numero_dps)
        etree.SubElement(inf_dps, "dCompet").text = datetime.now().strftime("%Y-%m-%d")
        etree.SubElement(inf_dps, "tpEmit").text = "1" # Prestador
        etree.SubElement(inf_dps, "cLocEmi").text = self.empresa.codigo_municipio_ibge
        
        # Bloco do Prestador
        prest = etree.SubElement(inf_dps, "prest")
        etree.SubElement(prest, "CNPJ").text = self.empresa.cnpj
        
        # Bloco do Tomador (Cliente)
        tom = etree.SubElement(inf_dps, "tom")
        doc_type = "CNPJ" if len(self.nota.cliente.document) > 11 else "CPF"
        etree.SubElement(tom, doc_type).text = self.nota.cliente.document
        
        # Bloco de Serviço (Resumo)
        serv = etree.SubElement(inf_dps, "serv")
        # Usa o CNAE do serviço ou o padrão da empresa
        cnae = self.servico.get('codigo_cnae') or self.empresa.cnae_padrao
        etree.SubElement(serv, "cServ").text = cnae
        
        # Valores
        vals = etree.SubElement(inf_dps, "vals")
        etree.SubElement(vals, "vServPrest").text = "{:.2f}".format(self.nota.valor_total)
        
        return etree.tostring(dps, encoding='unicode')

def assinar_xml(xml_string, cert_base64, senha):
    """
    Signs the XML string using the provided A1 certificate in base64.
    """
    if not cert_base64 or not senha:
        raise ValueError("Certificado e senha são obrigatórios para assinatura.")
        
    p12_data = base64.b64decode(cert_base64)
    # Note: Modern cryptography versions use load_key_and_certificates
    key, cert, additional_certs = load_key_and_certificates(p12_data, senha.encode())
    
    root = etree.fromstring(xml_string.encode('utf-8'))
    # Sign XML
    signer = XMLSigner()
    signed_root = signer.sign(root, key=key, cert=cert)
    
    return etree.tostring(signed_root, encoding='unicode')

import requests

def enviar_para_recife(xml_assinado):
    """
    Sends the signed XML to the Recife WebService via SOAP.
    """
    url = "https://nfse-homologacao.recife.pe.gov.br/WsNFeNacional/Lote.asmx"
    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "SOAPAction": "http://www.sped.fazenda.gov.br/nfse/EnviarLoteDPS"
    }
    
    # Envelope SOAP conforme manual
    # XML inside <arquivo> must be escaped if sent inside the text node, 
    # but the manual might expect CDATA or a specific wrapping.
    # Using a f-string for simplicity as suggested in the snippet.
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <EnviarLoteDPSRequest xmlns="http://www.sped.fazenda.gov.br/nfse">
          <arquivo>{xml_assinado}</arquivo>
        </EnviarLoteDPSRequest>
      </soap12:Body>
    </soap12:Envelope>"""

    response = requests.post(url, data=soap_envelope.encode('utf-8'), headers=headers)
    return response.text

def emitir_nfse(invoice):
    """
    Orchestrates the NFSe emission process for a given Invoice.
    """
    empresa = EmpresaFiscal.objects.first()
    if not empresa or not empresa.certificado_a1_base64:
        raise ValueError("Empresa fiscal não configurada ou sem certificado.")

    with transaction.atomic():
        # 1. Get or Create NotaFiscalServico
        try:
             # Check if related_name access works
             nota = invoice.nfs_record
             if not nota:
                 raise NotaFiscalServico.DoesNotExist
             created = False
        except (AttributeError, NotaFiscalServico.DoesNotExist):
             nota = NotaFiscalServico.objects.create(
                numero_dps=empresa.ultimo_numero_dps + 1,
                serie="1",
                invoice=invoice,
                cliente=invoice.client,
                valor_total=invoice.amount,
                status='processando'
            )
             created = True
        
        if created:
            empresa.ultimo_numero_dps += 1
            empresa.save()
            
        # 2. Prepare Data
        servico_data = {
            'codigo_cnae': empresa.cnae_padrao,
            'discriminacao': f"Fatura {invoice.number}"
        }
        
        # 3. Generate XML
        generator = DPSGenerator(empresa, nota, servico_data)
        xml_bruto = generator.gerar_xml_bruto()
        
        # 4. Sign XML
        xml_assinado = assinar_xml(xml_bruto, empresa.certificado_a1_base64, empresa.senha_certificado)
        
        # 5. Send/Save
        nota.xml_enviado = xml_assinado
        # TODO: Post to Recife
        nota.status = 'emitida' 
        nota.save()
        
        return nota
