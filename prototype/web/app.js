'use strict';
const $=id=>document.getElementById(id);
const fmt=p=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP'}).format((p||0)/100);
const textNode=(tag,value,cls='')=>{const el=document.createElement(tag);el.textContent=String(value??'');if(cls)el.className=cls;return el;};
function status(msg,isError=false){$('message').textContent=msg;$('message').className=isError?'error':'positive';}
async function api(method,path,payload){
 const opts={method,headers: {'Accept':'application/json'}};
 if(payload!==undefined){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(payload);}
 const res=await fetch(path,opts);
 let data;try{data=await res.json();}catch{throw Error('Unexpected server response.');}
 if(!res.ok)throw Error(data.error||'Request failed');
 return data;
}
function show(section){
 for(const name of ['customer','owner','rules','appearance'])$(name).classList.toggle('hidden',name!==section);
 for(const [id,name] of [['showCustomer','customer'],['showOwner','owner'],['showRules','rules'],['showAppearance','appearance']])$(id).className=name===section?'':'secondary';
 status('');
 if(section==='owner')loadEnquiries();
 if(section==='rules')loadRates();
}
$('showCustomer').onclick=()=>show('customer');
$('showOwner').onclick=()=>show('owner');
$('showRules').onclick=()=>show('rules');
$('showAppearance').onclick=()=>show('appearance');
$('service').addEventListener('change',()=>{
 if($('service').value==='patio'&&$('surface').value==='block_paving')$('surface').value='patio_slabs';
 if($('service').value==='patio')$('resanding').checked=false;
});
$('surface').addEventListener('change',()=>{if($('surface').value!=='block_paving')$('resanding').checked=false;});
function job(){return {service:$('service').value,surface:$('surface').value,condition:$('condition').value,
 area_m2:$('area').value,biocide:$('biocide').checked,resanding:$('resanding').checked};}
function renderQuote(e){
 $('quoteTotal').textContent=fmt(e.total_pence);
 $('lines').replaceChildren();
 for(const line of e.line_items){
  const row=document.createElement('div');row.className='line';
  row.append(textNode('span',line.label),textNode('b',fmt(line.pence)));
  $('lines').append(row);
 }
 $('flags').replaceChildren();
 for(const message of e.review_flags)$('flags').append(textNode('p',message));
}
async function preview(){
 try{const r=await api('POST','/api/estimate',job());renderQuote(r.estimate);status('Draft calculated — owner approval still required.');}
 catch(e){status(e.message,true);$('quoteTotal').textContent='—';}
}
$('estimateBtn').onclick=preview;
$('jobForm').addEventListener('submit',async event=>{
 event.preventDefault();
 if(!$('jobForm').reportValidity())return;
 try{
  const body={customer_name:$('name').value.trim(),postcode:$('postcode').value,description:$('description').value.trim(),
   job:job(),fictional_data_only:$('fictional').checked};
  const res=await api('POST','/api/enquiries',body);
  renderQuote(res.enquiry.estimate);
  status('Fictional enquiry #'+res.enquiry.id+' saved for owner review. No message was sent.');
 }catch(e){status(e.message,true);}
});
let localPreviewUrl;
$('photo').addEventListener('change',event=>{
 if(localPreviewUrl)URL.revokeObjectURL(localPreviewUrl);
 const file=event.target.files?.[0];$('photoPreview').classList.toggle('hidden',!file);
 if(file&&file.type.startsWith('image/')&&file.size<=5_000_000){
  localPreviewUrl=URL.createObjectURL(file);$('photoPreview').src=localPreviewUrl;
 }else{$('photoPreview').classList.add('hidden');if(file)status('Image preview supports image files up to 5 MB.',true);}
});
async function loadEnquiries(){
 try{
  const data=await api('GET','/api/enquiries');
  const box=$('enquiries');box.replaceChildren();
  if(!data.enquiries.length){box.append(textNode('p','No fictional enquiries yet.'));return;}
  for(const e of data.enquiries){
   const card=document.createElement('div');card.className='card';
   card.append(textNode('h3','#'+e.id+' · '+e.customer_name+' · '+e.postcode));
   card.append(textNode('p',e.description,'muted'));
   card.append(textNode('p',e.status.replaceAll('_',' '),'pill'));
   card.append(textNode('p','Draft: '+fmt(e.estimate.total_pence)));
   for(const f of e.estimate.review_flags)card.append(textNode('p',f,'small muted'));
   if(e.status==='awaiting_owner'){
    const price=document.createElement('input');price.type='number';price.min='0.01';price.step='0.01';price.value=(e.estimate.total_pence/100).toFixed(2);
    price.setAttribute('aria-label','Approved total in pounds');
    const note=document.createElement('input');note.maxLength=500;note.placeholder='Owner note (optional)';note.setAttribute('aria-label','Owner review note');
    const approve=textNode('button','Approve sample');const reject=textNode('button','Reject sample','warn');
    approve.onclick=()=>review(e.id,'approve',price.value,note.value);
    reject.onclick=()=>review(e.id,'reject',null,note.value);
    card.append(price,note,approve,reject);
   }else if(e.approved_total_pence!==null)card.append(textNode('p','Approved price: '+fmt(e.approved_total_pence)));
   box.append(card);
  }
 }catch(e){status(e.message,true);}
}
async function review(id,action,price,note){
 try{
  let body;
  if(action==='approve'){
   const val=Number(price);
   if(!Number.isFinite(val)||val<=0||!Number.isInteger(Math.round(val*100))||Math.round(val*100)>10000000)throw Error('Enter a valid approved price.');
   body={approved_total_pence:Math.round(val*100),note};
  }else body={note};
  await api('POST','/api/enquiries/'+id+'/'+action,body);
  status('Fictional enquiry #'+id+' reviewed. No customer was contacted.');
  await loadEnquiries();
 }catch(e){status(e.message,true);}
}
$('refresh').onclick=loadEnquiries;
const fields=[
 ['per_m2','Washing per m² (£)'],['minimum','Minimum charge (£)'],['biocide_flat','Biocide treatment (£)'],
 ['resand_flat','Re-sanding (£)'],['moderate_percent','Moderate condition (%)'],['heavy_percent','Heavy condition (%)'],['vat_percent','VAT rate (%)']
];
async function loadRates(){
 try{
  const data=await api('GET','/api/rates');$('rateFields').replaceChildren();
  for(const [key,label] of fields){
   const wrap=document.createElement('div');wrap.className='field';
   const l=document.createElement('label');l.htmlFor='rate_'+key;l.textContent=label;
   const input=document.createElement('input');input.type='number';input.step='.01';input.min='0';input.id='rate_'+key;
   input.value=data.rates[key];wrap.append(l,input);$('rateFields').append(wrap);
  }
  $('vat_enabled').checked=data.rates.vat_enabled;
 }catch(e){status(e.message,true);}
}
$('ratesForm').addEventListener('submit',async event=>{
 event.preventDefault();
 const rates={vat_enabled:$('vat_enabled').checked};
 for(const [key] of fields)rates[key]=$('rate_'+key).value;
 try{await api('POST','/api/rates',rates);status('Demo rates saved. Existing quotations retain their pricing snapshots.');}
 catch(e){status(e.message,true);}
});
preview();
