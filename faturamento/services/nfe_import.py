import xml.etree.ElementTree as ET
from datetime import datetime
from django.utils import timezone
from core.models import Person
from estoque.models import Product, Brand, Category  # Assuming these exist
from faturamento.models import NotaEntrada, NotaEntradaItem, NotaEntradaParcela

def processar_xml_nfe(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Namespaces usually exist in NFe, we need to handle them or ignore them
    # NFe namespace: {http://www.portalfiscal.inf.br/nfe}
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # 1. Parse Emission Info
    infNFe = root.find('.//nfe:infNFe', ns)
    if infNFe is None:
         # Try without namespace if failed (sometimes XMLs are stripped)
         ns = {}
         infNFe = root.find('.//infNFe')
    
    ide = infNFe.find('nfe:ide', ns)
    emit = infNFe.find('nfe:emit', ns)
    total = infNFe.find('nfe:total/nfe:ICMSTot', ns)
    
    chave_acesso = infNFe.attrib.get('Id', '')[3:] # Remove 'NFe' prefix

    # 1a. Check for Duplicates
    if NotaEntrada.objects.filter(chave_acesso=chave_acesso).exists():
        raise ValueError(f"Nota Fiscal com chave {chave_acesso} já foi importada.")

    numero_nota = ide.find('nfe:nNF', ns).text
    serie = ide.find('nfe:serie', ns).text
    data_emissao_str = ide.find('nfe:dhEmi', ns).text
    # Parse date (ISO format usually: 2023-10-25T14:30:00-03:00)
    data_emissao = datetime.fromisoformat(data_emissao_str).date()
    
    valor_total = total.find('nfe:vNF', ns).text
    
    # 2. Find or Create Supplier
    cnpj_emit = emit.find('nfe:CNPJ', ns).text
    razao_social = emit.find('nfe:xNome', ns).text
    nome_fantasia = emit.find('nfe:xFant', ns).text if emit.find('nfe:xFant', ns) is not None else razao_social
    
    # Address info
    enderEmit = emit.find('nfe:enderEmit', ns)
    logradouro = enderEmit.find('nfe:xLgr', ns).text
    numero = enderEmit.find('nfe:nro', ns).text
    bairro = enderEmit.find('nfe:xBairro', ns).text
    municipio = enderEmit.find('nfe:xMun', ns).text
    uf = enderEmit.find('nfe:UF', ns).text
    cep = enderEmit.find('nfe:CEP', ns).text
    
    supplier, created = Person.objects.get_or_create(
        document=cnpj_emit,
        defaults={
            'name': razao_social,
            'fantasy_name': nome_fantasia,
            'person_type': 'PJ',
            'is_supplier': True,
            'address': logradouro,
            'number': numero,
            'neighborhood': bairro,
            'city': municipio,
            'state': uf,
            'zip_code': cep
        }
    )
    
    if not supplier.is_supplier:
        supplier.is_supplier = True
        supplier.save()

    # 3. Create NotaEntrada
    nota = NotaEntrada.objects.create(
        fornecedor=supplier,
        chave_acesso=chave_acesso,
        numero_nota=numero_nota,
        serie=serie,
        data_emissao=data_emissao,
        valor_total=valor_total,
        arquivo_xml=xml_file,
        status='IMPORTADA'
    )
    
    # 3a. Extract and Create Parcelas
    duplicatas = extract_duplicatas(xml_file)
    if duplicatas:
        for dup in duplicatas:
            NotaEntradaParcela.objects.create(
                nota=nota,
                numero_parcela=dup['number'],
                data_vencimento=dup['due_date'],
                valor=dup['amount']
            )
    else:
        # If no duplicates, assume single parcel (create one for review)
        NotaEntradaParcela.objects.create(
            nota=nota,
            numero_parcela='001',
            data_vencimento=data_emissao, # Default to issue date or today
            valor=valor_total,
            forma_pagamento='OUTROS' # Default
        )

    # 4. Process Items
    dets = infNFe.findall('nfe:det', ns)
    for det in dets:
        prod = det.find('nfe:prod', ns)
        imposto = det.find('nfe:imposto', ns)
        
        cProd = prod.find('nfe:cProd', ns).text
        cEAN = prod.find('nfe:cEAN', ns).text
        xProd = prod.find('nfe:xProd', ns).text
        NCM = prod.find('nfe:NCM', ns).text
        CFOP = prod.find('nfe:CFOP', ns).text
        uCom = prod.find('nfe:uCom', ns).text
        qCom = prod.find('nfe:qCom', ns).text
        vUnCom = prod.find('nfe:vUnCom', ns).text
        vProd = prod.find('nfe:vProd', ns).text
        
        # Try to find product by EAN or SKU
        produto = None
        if cEAN and cEAN != 'SEM GTIN' and cEAN.strip():
            produto = Product.objects.filter(sku=cEAN).first()
            
        if not produto and cProd:
            produto = Product.objects.filter(sku=cProd).first()
            
        # Just store the XML data in the item
            
        NotaEntradaItem.objects.create(
            nota=nota,
            produto=produto, # Can be None now
            quantidade=qCom,
            valor_unitario=vUnCom,
            valor_total=vProd,
            cfop=CFOP,
            xProd=xProd[:255],
            cProd=cProd[:60],
            cEAN=cEAN[:14] if cEAN else None
        )
        
    return nota
    
def extract_duplicatas(xml_file):
    # Pass just path if it's a field file, handled by ET.parse?
    # ET.parse accepts file path or file-like object. 
    # If xml_file is a FieldFile, use .path or .open()
    try:
        if hasattr(xml_file, 'path'):
            source = xml_file.path
        else:
            source = xml_file
        tree = ET.parse(source)
    except:
        # Retry with seek 0 if it's an open file
        if hasattr(xml_file, 'seek'):
            xml_file.seek(0)
        tree = ET.parse(xml_file)
        
    root = tree.getroot()
    root = tree.getroot()
    
    # NFe namespace
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Try with and without namespace
    cobr = root.find('.//nfe:cobr', ns)
    if cobr is None:
         ns = {}
         cobr = root.find('.//cobr')
         
    duplicatas = []
    
    if cobr is not None:
        dups = cobr.findall('nfe:dup', ns) if 'nfe' in ns else cobr.findall('dup')
        for dup in dups:
            nDup = dup.find('nfe:nDup', ns).text if 'nfe' in ns else dup.find('nDup').text
            dVenc_str = dup.find('nfe:dVenc', ns).text if 'nfe' in ns else dup.find('dVenc').text
            vDup = dup.find('nfe:vDup', ns).text if 'nfe' in ns else dup.find('vDup').text
            
            try:
                dVenc = datetime.strptime(dVenc_str, '%Y-%m-%d').date()
            except ValueError:
                dVenc = timezone.now().date() # Fallback
                
            duplicatas.append({
                'number': nDup,
                'due_date': dVenc,
                'amount': vDup
            })
            
    return duplicatas
