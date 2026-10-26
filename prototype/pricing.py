"""Deterministic owner-configurable UK exterior-cleaning quotation draft engine.
Photos and AI never determine prices or infer dimensions.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

QUOTE_VERSION=1
SERVICES=('driveway','patio')
SURFACES=('block_paving','concrete','patio_slabs','other')
CONDITIONS=('light','moderate','heavy')
AREAS=('HA1','HA2','HA3','HA5','UB5')
DEFAULT_RATES={
 'per_m2':'2.50','minimum':'60.00','biocide_flat':'35.00','resand_flat':'50.00',
 'moderate_percent':'15.00','heavy_percent':'35.00','vat_percent':'20.00','vat_enabled':False
}
RANGES={'per_m2':('0.01','500'),'minimum':('0','10000'),'biocide_flat':('0','10000'),
 'resand_flat':('0','10000'),'moderate_percent':('0','300'),'heavy_percent':('0','300'),
 'vat_percent':('0','100')}

class InputError(ValueError):
    """Invalid fictional enquiry input or owner pricing."""

def amount(value):
    if isinstance(value,bool) or not isinstance(value,(int,float,str,Decimal)):
        raise InputError('A numeric amount was expected.')
    try:
        val=Decimal(str(value))
    except InvalidOperation:
        raise InputError('Enter a valid number.') from None
    if not val.is_finite():
        raise InputError('The number must be finite.')
    return val

def cents(value):
    return int((value*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def currency(value):
    return format(Decimal(cents(value))/100,'.2f')

def validate_rates(payload):
    if not isinstance(payload,dict) or set(payload)!=set(DEFAULT_RATES):
        raise InputError('Provide exactly the supported pricing fields.')
    clean={}
    for k,(lo,hi) in RANGES.items():
        val=amount(payload[k])
        if not Decimal(lo)<=val<=Decimal(hi):
            raise InputError(f'{k} is outside its permitted range.')
        clean[k]=currency(val)
    if type(payload['vat_enabled']) is not bool:
        raise InputError('vat_enabled must be true or false.')
    clean['vat_enabled']=payload['vat_enabled']
    return clean

def validate_job(payload):
    if not isinstance(payload,dict):
        raise InputError('Expected a quotation request.')
    service=payload.get('service')
    surface=payload.get('surface')
    condition=payload.get('condition')
    if service not in SERVICES:
        raise InputError('Select driveway or patio.')
    if surface not in SURFACES or condition not in CONDITIONS:
        raise InputError('Choose an available surface and condition.')
    if service=='patio' and surface=='block_paving':
        raise InputError('Choose driveway for block paving, or select another surface.')
    area=amount(payload.get('area_m2'))
    if not Decimal('1')<=area<=Decimal('2000'):
        raise InputError('Area must be between 1 and 2,000 m².')
    if area.as_tuple().exponent < -2:
        raise InputError('Area can have at most two decimal places.')
    b,s=payload.get('biocide',False),payload.get('resanding',False)
    if type(b) is not bool or type(s) is not bool:
        raise InputError('Treatment choices must be true or false.')
    if s and surface!='block_paving':
        raise InputError('Re-sanding is available only for block paving.')
    return {'service':service,'surface':surface,'condition':condition,
            'area_m2':str(area),'biocide':b,'resanding':s}

def estimate(job,rates):
    job=validate_job(job)
    rates=validate_rates(rates)
    area=amount(job['area_m2'])
    base=max(area*amount(rates['per_m2']),amount(rates['minimum']))
    lines=[{'label':'Cleaning (minimum applied where required)','pence':cents(base)}]
    pct=amount(rates['moderate_percent'] if job['condition']=='moderate' else rates['heavy_percent'] if job['condition']=='heavy' else '0')
    if pct:
        lines.append({'label':f"{job['condition'].title()} condition surcharge ({pct.normalize()}%)",
                      'pence':cents(base*pct/100)})
    if job['biocide']:
        lines.append({'label':'Biocide treatment','pence':cents(amount(rates['biocide_flat']))})
    if job['resanding']:
        lines.append({'label':'Block paving re-sanding','pence':cents(amount(rates['resand_flat']))})
    subtotal=sum(x['pence'] for x in lines)
    vat=cents(Decimal(subtotal)/100*amount(rates['vat_percent'])/100) if rates['vat_enabled'] else 0
    if rates['vat_enabled']:
        lines.append({'label':f"VAT ({rates['vat_percent']}%)",'pence':vat})
    flags=['Owner approval required before any customer quotation.']
    if job['surface']=='other': flags.append('Unrecognised surface: inspection may be necessary.')
    if job['condition']=='heavy': flags.append('Heavy staining: verify treatment and labour on site.')
    if area>150: flags.append('Large area: verify measurements and access.')
    if job['resanding']: flags.append('Verify joints and re-sanding quantity before approval.')
    return {'quote_version':QUOTE_VERSION,'job':job,'pricing_snapshot':rates,'line_items':lines,
            'subtotal_pence':subtotal,'vat_pence':vat,'total_pence':subtotal+vat,'review_flags':flags,
            'status':'draft_requires_owner_review','photo_analysis':'not_available',
            'notice':'Indicative draft; no dimensions inferred from photos and no quote sent.'}

def validate_enquiry(payload):
    if not isinstance(payload,dict): raise InputError('Expected an enquiry.')
    name=payload.get('customer_name','')
    description=payload.get('description','')
    if not isinstance(name,str) or not 2<=len(name.strip())<=60:
        raise InputError('Enter a fictional name between 2 and 60 characters.')
    if not isinstance(description,str) or not 8<=len(description.strip())<=1000:
        raise InputError('Enter a description between 8 and 1,000 characters.')
    postcode=payload.get('postcode')
    if postcode not in AREAS: raise InputError('Choose a pilot postcode district.')
    if payload.get('fictional_data_only') is not True:
        raise InputError('This local demo accepts fictional information only.')
    job=validate_job(payload.get('job'))
    return {'customer_name':name.strip(),'description':description.strip(),'postcode':postcode,'job':job}

def validate_approval(payload):
    if not isinstance(payload,dict) or set(payload)!={'approved_total_pence','note'}:
        raise InputError('Approval requires an amount and review note.')
    value=payload['approved_total_pence']
    if isinstance(value,bool) or type(value) is not int or not 0<value<=10_000_000:
        raise InputError('Approved price must be between £0.01 and £100,000.')
    note=payload['note']
    if not isinstance(note,str) or len(note.strip())>500:
        raise InputError('Approval note cannot exceed 500 characters.')
    return value,note.strip()
