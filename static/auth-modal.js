(()=>{
const overlay=document.getElementById('ep-auth-overlay');if(!overlay)return;
const $=id=>document.getElementById(id),details=$('ep-auth-details'),verify=$('ep-auth-verify');
let mode='register',step='details',seconds=0,timer=null,returnFocus=null,redirectTo='';
function alertMessage(message){$('ep-auth-alert').textContent=message;$('ep-auth-alert').hidden=!message;}
function update(){
 const register=mode==='register',otp=step==='verify';
 $('ep-auth-eyebrow').textContent=register?'JOIN OUR COMMUNITY':'WELCOME BACK';
 $('ep-auth-title').textContent=otp?'Verify OTP':register?'Create your account':'Sign in';
 $('ep-auth-subtitle').textContent=otp?'Enter the 6-digit code sent to your mobile number':register?'Make your ritual booking journey a little simpler.':'Continue your ritual booking journey.';
 $('ep-auth-steps').hidden=!register&&!otp;
 $('ep-step-one').textContent=otp?'✓':'1';$('ep-step-one').classList.toggle('active',!otp);
 $('ep-step-two').classList.toggle('active',otp);
 details.hidden=otp;verify.hidden=!otp;
 details.querySelectorAll('.ep-register-only').forEach(el=>{el.hidden=!register;el.querySelector('input').required=register;});
 $('ep-auth-mode').value=mode;$('ep-auth-verify-button').textContent=register?'Create account →':'Verify & sign in →';
 $('ep-auth-switch').hidden=otp;
 $('ep-auth-switch').innerHTML=register?'Already have an account? <button type="button" data-auth-switch="login">Sign in</button>':'New here? <button type="button" data-auth-switch="register">Create an account</button>';
}
function open(which='login',next=''){returnFocus=document.activeElement;mode=which;step='details';redirectTo=next||window.location.pathname;details.reset();verify.reset();alertMessage('');update();overlay.hidden=false;document.body.classList.add('ep-auth-open');overlay.querySelector('.ep-auth-dialog').focus();}
function close(){overlay.hidden=true;document.body.classList.remove('ep-auth-open');clearInterval(timer);if(returnFocus?.focus)returnFocus.focus();}
async function post(url,form){const response=await fetch(url,{method:'POST',body:form,credentials:'same-origin',headers:{'Accept':'application/json'}});let data;try{data=await response.json()}catch{throw new Error('Unable to contact the server. Please try again.')}if(!response.ok||!data.ok)throw new Error(data.error||'Request failed.');return data;}
function countdown(){clearInterval(timer);seconds=30;const tick=()=>{$('ep-resend').disabled=seconds>0;$('ep-resend-countdown').textContent=seconds>0?'in 00:'+String(seconds).padStart(2,'0'):'';seconds--;if(seconds<0)clearInterval(timer);};tick();timer=setInterval(tick,1000);}
details.addEventListener('submit',async e=>{e.preventDefault();alertMessage('');const button=details.querySelector('[type=submit]');button.disabled=true;try{const result=await post('/auth/otp/send',new FormData(details));step='verify';update();$('ep-otp-phone').textContent=result.phone;verify.reset();countdown();$('ep-otp-code').focus();}catch(error){alertMessage(error.message)}finally{button.disabled=false;}});
verify.addEventListener('submit',async e=>{e.preventDefault();alertMessage('');const button=$('ep-auth-verify-button');button.disabled=true;const form=new FormData(verify);form.set('next',redirectTo);try{const result=await post('/auth/otp/verify',form);window.location.assign(result.redirect||'/account');}catch(error){alertMessage(error.message);button.disabled=false;}});
$('ep-resend').addEventListener('click',()=>details.requestSubmit());$('ep-auth-back').addEventListener('click',()=>{step='details';alertMessage('');update();});
overlay.addEventListener('click',e=>{if(e.target===overlay||e.target.closest('.ep-auth-close'))close();const sw=e.target.closest('[data-auth-switch]');if(sw){mode=sw.dataset.authSwitch;step='details';alertMessage('');update();}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!overlay.hidden)close();if(e.key==='Tab'&&!overlay.hidden){const els=[...overlay.querySelectorAll('button:not(:disabled),input:not(:disabled)')].filter(el=>el.getClientRects().length);if(!els.length)return;const first=els[0],last=els.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}});
document.addEventListener('click',e=>{const link=e.target.closest('a[href]');if(!link||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||link.target==='_blank')return;const u=new URL(link.href,location.href);if(u.origin!==location.origin)return;if(u.pathname==='/login'||u.pathname==='/register'){e.preventDefault();open(u.pathname==='/register'?'register':'login',u.searchParams.get('next')||location.pathname);}});
const query=new URLSearchParams(location.search);if(query.has('auth')){open(query.get('auth')==='register'?'register':'login',query.get('next')||'/account');history.replaceState(null,'',location.pathname);}
})();
