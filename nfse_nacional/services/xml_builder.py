from django.template.loader import render_to_string
from nfse_nacional.models import NFSe

def renderizar_xml_dps(nfse_obj: NFSe) -> str:
    """
    Renderiza o XML da DPS (Declaração de Prestação de Serviço)
    baseado no objeto NFSe fornecido.
    """
    # Clean taxation codes
    c_trib_nac = nfse_obj.servico.codigo_tributacao_nacional
    if c_trib_nac:
        # Filter digits only to remove dots, dashes or accidental letters (like 'l' instead of '1')
        c_trib_nac = "".join(filter(str.isdigit, c_trib_nac))
        
        # Ensure exactly 6 digits (Padrão Nacional 1.01)
        # For item 1.07.01, it should be 010701.
        if len(c_trib_nac) > 0 and len(c_trib_nac) < 6:
            # If it's like "0107", assume "010700" (back-padding) 
            # OR if it's like "10701", assume "010701" (front-padding).
            # The most common failure for 1.07.01 is being sent as 10701 (5 chars).
            if len(c_trib_nac) == 5:
                c_trib_nac = c_trib_nac.zfill(6)
            elif len(c_trib_nac) == 4:
                c_trib_nac += "00"
            else:
                c_trib_nac = c_trib_nac.zfill(6)
        
    c_trib_mun = nfse_obj.servico.codigo_tributacao_municipal
    if c_trib_mun:
        c_trib_mun = c_trib_mun.strip()
        # If dots are present (e.g., 14.02.01.501), take the last segment (the complement)
        if '.' in c_trib_mun:
            c_trib_mun = c_trib_mun.split('.')[-1]
        # Extract only digits
        c_trib_mun = "".join(filter(str.isdigit, c_trib_mun))
        
    c_nbs = nfse_obj.servico.codigo_nbs
    if c_nbs:
        c_nbs = c_nbs.replace('.', '').replace('-', '')

    # Clean CNPJ/CPF
    prestador_cnpj = nfse_obj.empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
    tomador_doc_clean = nfse_obj.cliente.document.replace('.', '').replace('/', '').replace('-', '')
    
    tomador_cpf = ''
    tomador_cnpj = ''
    if len(tomador_doc_clean) == 11:
        tomador_cpf = tomador_doc_clean
    else:
        tomador_cnpj = tomador_doc_clean

    # Format values
    def format_decimal(value):
        return f"{value:.2f}"

    # Build service description (append complementary info if present)
    desc_serv = nfse_obj.servico.description or nfse_obj.servico.name
    if nfse_obj.inf_adic:
        desc_serv = f"{desc_serv} | {nfse_obj.inf_adic}"
    # Truncate to 2000 chars (xDescServ limit)
    desc_serv = desc_serv[:2000]

    # Updated to use override fields
    sale_price = nfse_obj.valor_servico if nfse_obj.valor_servico else nfse_obj.servico.sale_price
    
    v_serv = format_decimal(sale_price)
    p_iss = format_decimal(nfse_obj.servico.aliquota_iss)
    
    # Calculate vISS
    v_iss_val = (sale_price * nfse_obj.servico.aliquota_iss) / 100
    v_iss = format_decimal(v_iss_val)
    
    # Calculate vLiq (Net Value) - Assuming no discounts for now
    v_liq = v_serv

    # Generate DPS ID
    # Pattern: DPS + CodMun(7) + TipoInsc(1) + Inscricao(14) + Serie(5) + NumDPS(15)
    cod_mun_ibge = nfse_obj.empresa.codigo_mun_ibge
    tipo_insc = "2" # CNPJ (EuGestor uses 2)
    inscr_federal = prestador_cnpj
    serie_str = f"{int(nfse_obj.serie_dps):05d}"
    num_dps_str = f"{nfse_obj.numero_dps:015d}"
    
    inf_dps_id = f"DPS{cod_mun_ibge}{tipo_insc}{inscr_federal}{serie_str}{num_dps_str}"

    # Format Date with Timezone (TSDateTimeUTC)
    # Format: YYYY-MM-DDThh:mm:ss-HH:MM (Explicit offset with colon)
    from datetime import timedelta, timezone
    
    # Define timezone UTC-3 (Recife/Brasilia)
    tz_br = timezone(timedelta(hours=-3))

    dt_emi = nfse_obj.data_emissao
    
    # Ensure timezone awareness
    if dt_emi.tzinfo is None:
        dt_emi = dt_emi.replace(tzinfo=tz_br)
    else:
        dt_emi = dt_emi.astimezone(tz_br)

    # Check if emission date is in the future and clamp it
    from django.utils import timezone as django_timezone
    now_br = django_timezone.now().astimezone(tz_br)
    
    if dt_emi > now_br:
        dt_emi = now_br

    # Format: YYYY-MM-DDThh:mm:ss%z (gives -0300)
    dh_emi_str = dt_emi.replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%S%z')
    
    # Insert colon in timezone offset (-0300 -> -03:00)
    dh_emi_formatted = dh_emi_str[:-2] + ":" + dh_emi_str[-2:]
    
    # Also format competence date from the SAME (clamped) dt_emi
    d_compet_formatted = dt_emi.strftime('%Y-%m-%d')

    # Tax Regime Logic
    # opSimpNac: 1=Não Optante, 2=MEI, 3=ME/EPP (Simples Nacional)
    # regApTribSN: 1=Simples Nacional (Federais+Municipal), 2=Federais SN + ISS NFS-e, 3=NFS-e (Fora SN)
    
    # Defaulting to Simples Nacional ME/EPP (3) and Regime 1 (All SN) as per user request
    if hasattr(nfse_obj.empresa, 'optante_simples'):
        # If explicitly set in model, map it. But for now, user requested specific values.
        # Let's stick to the requested fix: opSimpNac=3, regApTribSN=1
        op_simp_nac = '3' 
    else:
        op_simp_nac = '3' 

    if hasattr(nfse_obj.empresa, 'regime_tributario'):
        # Map model values if needed, but for now force 1
        reg_ap_trib_sn = '1'
    else:
        reg_ap_trib_sn = '1'

    # Regime Especial de Tributação
    # 0 = Nenhum
    if hasattr(nfse_obj.empresa, 'regime_especial_tributacao'):
         reg_esp_trib = str(nfse_obj.empresa.regime_especial_tributacao)
    else:
         reg_esp_trib = '0'

    # Tomador Município Logic
    tomador_c_mun = nfse_obj.cliente.codigo_municipio_ibge
    if not tomador_c_mun:
        tomador_c_mun = nfse_obj.empresa.codigo_mun_ibge

    # Clean Phone (Tomador)
    # Clean Phone (Tomador)
    tomador_fone = ''
    if nfse_obj.cliente.phone:
        tomador_fone = ''.join(filter(str.isdigit, nfse_obj.cliente.phone))
        # Remove country code 55 if present and length > 11
        if len(tomador_fone) > 11 and tomador_fone.startswith('55'):
            tomador_fone = tomador_fone[2:]
        # Take at most 11 chars (DDD + Number)
        tomador_fone = tomador_fone[:11]

    # Clean Phone (Prestador)
    prest_fone = ''
    # Assuming 'phone' field exists in Empresa model, if not, handle gracefully
    if hasattr(nfse_obj.empresa, 'phone') and nfse_obj.empresa.phone:
         prest_fone = ''.join(filter(str.isdigit, nfse_obj.empresa.phone))
         if len(prest_fone) > 11 and prest_fone.startswith('55'):
            prest_fone = prest_fone[2:]
         prest_fone = prest_fone[:11]
    
    prest_email = ''
    if hasattr(nfse_obj.empresa, 'email') and nfse_obj.empresa.email:
        prest_email = nfse_obj.empresa.email

    # Series Display (No leading zeros)
    serie_display = str(int(nfse_obj.serie_dps))

    context = {
        'nfse': nfse_obj,
        'c_trib_nac': c_trib_nac,
        'c_trib_mun': c_trib_mun,
        'c_nbs': c_nbs,
        'prestador_cnpj': prestador_cnpj,
        'tomador_cpf': tomador_cpf,
        'tomador_cnpj': tomador_cnpj,
        'tomador_c_mun': tomador_c_mun,
        'tomador_fone': tomador_fone,
        'prest_fone': prest_fone,
        'prest_email': prest_email,
        'tomador_endereco': {
            'logradouro': _sanitize(nfse_obj.cliente.address),
            'numero': _sanitize(nfse_obj.cliente.number),
            'complemento': _sanitize(nfse_obj.cliente.complement),
            'bairro': _sanitize(nfse_obj.cliente.neighborhood),
            'codigo_municipio': nfse_obj.cliente.codigo_municipio_ibge,
            'uf': nfse_obj.cliente.state,
            'cep': nfse_obj.cliente.zip_code.replace('.', '').replace('-', '') if nfse_obj.cliente.zip_code else '',
        },
        'v_serv': v_serv,
        'v_liq': v_liq,
        'p_iss': p_iss,
        'v_iss': v_iss,
        'inf_dps_id': inf_dps_id,
        'd_compet_formatted': d_compet_formatted,
        'serie_formatted': serie_display, # Tag <serie> without leading zeros
        'num_dps_simples': str(nfse_obj.numero_dps), # Tag <nDPS> without leading zeros
        'cod_mun_ibge': cod_mun_ibge,
        'dh_emi_formatted': dh_emi_formatted,
        'op_simp_nac': op_simp_nac,
        'reg_ap_trib_sn': reg_ap_trib_sn,
        'reg_esp_trib': reg_esp_trib,
        'trib_issqn': '1',  # 1=Tributável
        'c_loc_incid': cod_mun_ibge,  # Município de incidência do ISS
        'tp_ret_issqn': '1',  # 1=Não retido
        'desc_serv': desc_serv,
    }
    
    # Render the template
    xml_content = render_to_string('nfse/dps_padrao_nacional.xml', context)
    
    # Clean up whitespace and newlines (single continuous line)
    clean_xml = " ".join(xml_content.split())
    
    return clean_xml.strip()


def _sanitize(text):
    """Remove special chars that break XML schema validation."""
    if not text:
        return text
    s = str(text)
    # Replace XML-breaking chars
    s = s.replace('&', 'e').replace('<', '').replace('>', '')
    s = s.replace('#', '').replace('%', '').replace('"', '')
    # Collapse whitespace/newlines into single space
    s = ' '.join(s.split())
    return s.strip()
