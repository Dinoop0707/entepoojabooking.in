const $=s=>document.querySelector(s);
$('#menu-toggle')?.addEventListener('click',()=>{const nav=$('#main-nav');const open=nav.classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(open));});
$('#language')?.addEventListener('click',()=>alert('Malayalam translation is planned for a future release. This prototype currently uses English.'));
$('#service-chooser')?.addEventListener('change',e=>{const value=e.target.value;if(value){const form=e.target.closest('form');form.action='/services/'+value;}});
const date=$('#booking-date'),loc=$('#booking-district'),time=$('#booking-time'),svc=$('#booking-service');
function syncSummary(){if(!svc)return;const opt=svc.selectedOptions[0];$('#summary-name').textContent=opt.textContent;$('#summary-price').textContent='₹ '+Number(opt.dataset.price).toLocaleString('en-IN');$('#summary-image').src=opt.dataset.image;$('#summary-location').textContent=loc.value||'Not selected';$('#summary-date').textContent=date.value?new Date(date.value+'T12:00:00').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):'Not selected';$('#summary-time').textContent=time.value;}
[date,loc,time,svc].forEach(el=>el?.addEventListener('change',syncSummary));syncSummary();
$('#booking-form')?.addEventListener('submit',e=>{if(!e.target.reportValidity()){e.preventDefault();return;}if(!confirm('Save this booking request to the local demo? No payment will be collected and no priest will be booked.'))e.preventDefault();});
