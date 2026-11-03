/* ONECALL Design Studio — browser-local preferences only; no impact on quotes. */
'use strict';
(function(){
 const STORAGE='onecall_design_studio_v1';
 const keys={
  theme:['classic','midnight','violet','forest'],
  shape:['standard','square','soft'],
  density:['standard','compact','spacious'],
  type:['standard','small','large']
 };
 const defaults={theme:'classic',shape:'standard',density:'standard',type:'standard'};
 const doc=document.documentElement;
 let current={...defaults};
 function safe(value){
  if(!value||typeof value!=='object'||Array.isArray(value))return {...defaults};
  const out={...defaults};
  for(const key of Object.keys(keys)){
   if(keys[key].includes(value[key]))out[key]=value[key];
  }
  return out;
 }
 try{current=safe(JSON.parse(localStorage.getItem(STORAGE)||'null'));}catch{current={...defaults};}
 function apply(value){
  current=safe(value);
  for(const key of Object.keys(keys)){
   if(current[key]===defaults[key])doc.removeAttribute('data-'+key);
   else doc.setAttribute('data-'+key,current[key]);
  }
  for(const key of Object.keys(keys)){
   const selected=document.querySelector('input[name="'+key+'"][value="'+current[key]+'"]');
   if(selected)selected.checked=true;
  }
 }
 function message(value){const node=document.getElementById('designMessage');if(node)node.textContent=value;}
 document.addEventListener('DOMContentLoaded',()=>{
  apply(current);
  const form=document.getElementById('designForm');
  if(!form)return;
  form.addEventListener('change',event=>{
   const target=event.target;
   if(!target || !keys[target.name] || !keys[target.name].includes(target.value))return;
   apply({...current,[target.name]:target.value});
   message('Preview applied. Choose Save my design to remember it on this device.');
  });
  form.addEventListener('submit',event=>{
   event.preventDefault();
   try{localStorage.setItem(STORAGE,JSON.stringify(current));message('Design saved in this browser. Your quotations and pricing remain unchanged.');}
   catch{message('Unable to save on this device. The preview still works.');}
  });
  const reset=document.getElementById('resetDesign');
  reset?.addEventListener('click',()=>{
   apply(defaults);
   try{localStorage.removeItem(STORAGE);}catch{}
   message('Original appearance restored.');
  });
  const sample=document.getElementById('previewButton');
  sample?.addEventListener('click',()=>message('Sample button works. Design settings do not affect quote approvals.'));
 });
})();
