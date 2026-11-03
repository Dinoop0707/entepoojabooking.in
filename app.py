"""Kerala pooja booking concept - local Flask demo. No live priest availability or payments."""
import os, sqlite3, uuid, secrets, hmac, time, re, hashlib, logging
from urllib.parse import urlsplit
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import constants as site_config

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'local-preview-change-before-production')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1')
DB = ROOT / 'bookings.sqlite3'
DISTRICTS = ['Ernakulam','Thrissur','Thiruvananthapuram','Kozhikode','Kottayam','Palakkad','Alappuzha','Kannur','Kollam','Malappuram','Pathanamthitta','Wayanad','Idukki','Kasaragod']
SERVICES = [
 dict(slug='ganapathi-homam',name='Ganapathi Homam',category='Homam',short='Remove obstacles and welcome auspicious beginnings.',description='A traditional homam invoking Lord Ganesha, often performed before a new venture, housewarming or significant milestone.',price=5000,duration='2–3 hours',venue='Home / Temple',image='ganapathi.jpg',suitable=['New beginnings','New business','Education and career','Personal milestones']),
 dict(slug='griha-pravesham',name='Griha Pravesham Pooja',category='At Home',short='A meaningful blessing for your new home.',description='A traditional housewarming ceremony performed as your family enters a new home.',price=7500,duration='3–4 hours',venue='At Home',image='griha.jpg',suitable=['New homes','Moving day','Family blessings']),
 dict(slug='satyanarayana-pooja',name='Satyanarayana Pooja',category='Personal Rituals',short='A prayer for wellbeing, gratitude and harmony.',description='A devotional ceremony seeking blessings and expressing gratitude.',price=5000,duration='2–3 hours',venue='Home / Temple',image='homam.jpg',suitable=['Family occasions','Personal milestones','Thanksgiving']),
 dict(slug='vivaham',name='Vivaham',category='Marriage Rituals',short='Kerala wedding ceremonies rooted in tradition.',description='A ceremonial experience guided by traditional practices and family customs.',price=15000,duration='4–6 hours',venue='Home / Venue',image='vivaham.jpg',suitable=['Weddings','Marriage blessings']),
 dict(slug='pitru-karmam',name='Pitru Karmam',category='Ancestral Rites',short='Traditional prayers honouring ancestors.',description='Ancestral observances arranged respectfully, with consideration for family customs.',price=5000,duration='2–3 hours',venue='Home / Temple',image='pitru.jpg',suitable=['Remembrance','Ancestral observances']),
 dict(slug='temple-offerings',name='Temple Offerings',category='Temple Pooja',short='Offerings and rituals at participating temples.',description='Explore traditional temple offerings and request assistance arranging them.',price=2500,duration='1–2 hours',venue='At Temple',image='temple-offerings.jpg',suitable=['Temple visits','Special offerings']),
]
BY_SLUG = {s['slug']:s for s in SERVICES}

def init_db():
 with sqlite3.connect(DB) as con:
  con.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)''')
  columns=[r[1] for r in con.execute('PRAGMA table_info(users)')]
  if 'phone' not in columns: con.execute('ALTER TABLE users ADD COLUMN phone TEXT')
  con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone) WHERE phone IS NOT NULL')
  con.execute('''CREATE TABLE IF NOT EXISTS cart_items (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), service_slug TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity BETWEEN 1 AND 20), UNIQUE(user_id, service_slug))''')
  con.execute('''CREATE TABLE IF NOT EXISTS booking_orders (id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL, total INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Request received')''')
  con.execute('''CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL, service_slug TEXT NOT NULL, service_name TEXT NOT NULL, unit_price INTEGER NOT NULL, quantity INTEGER NOT NULL, line_total INTEGER NOT NULL)''')
  con.execute('''CREATE TABLE IF NOT EXISTS booking_requests (reference TEXT PRIMARY KEY, created_at TEXT NOT NULL, service TEXT NOT NULL, preferred_date TEXT NOT NULL, preferred_time TEXT NOT NULL, district TEXT NOT NULL, venue TEXT NOT NULL, full_name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT, address TEXT, notes TEXT)''')
  columns=[row[1] for row in con.execute('PRAGMA table_info(booking_requests)')]
  if 'user_id' not in columns: con.execute('ALTER TABLE booking_requests ADD COLUMN user_id INTEGER')
  if 'estimated_price' not in columns: con.execute('ALTER TABLE booking_requests ADD COLUMN estimated_price INTEGER')

@app.context_processor
def common():
 count=0
 if getattr(g,'user',None):
  with sqlite3.connect(DB) as con:
   count=con.execute('SELECT COALESCE(SUM(quantity),0) FROM cart_items WHERE user_id=?',(g.user['id'],)).fetchone()[0]
 return dict(districts=DISTRICTS,services=SERVICES,year=datetime.now().year,brand=site_config,current_user=g.user,csrf_token=session.get('csrf_token'),cart_count=count)

def require_user():
 if not g.user: return redirect(url_for('login',next=request.path))
 return None

def cart_for(user_id):
 with sqlite3.connect(DB) as con:
  con.row_factory=sqlite3.Row
  rows=con.execute('SELECT * FROM cart_items WHERE user_id=? ORDER BY id',(user_id,)).fetchall()
 items=[dict(id=r['id'],service=BY_SLUG[r['service_slug']],quantity=r['quantity'],line_total=BY_SLUG[r['service_slug']]['price']*r['quantity']) for r in rows if r['service_slug'] in BY_SLUG]
 return items,sum(x['line_total'] for x in items)


@app.before_request
def load_user():
 if 'csrf_token' not in session: session['csrf_token']=secrets.token_urlsafe(32)
 g.user=None
 if session.get('user_id'):
  init_db()
  with sqlite3.connect(DB) as con:
   con.row_factory=sqlite3.Row
   g.user=con.execute('SELECT id,full_name,email,phone FROM users WHERE id=?',(session['user_id'],)).fetchone()
  if not g.user: session.pop('user_id',None)
 if request.method=='POST' and not hmac.compare_digest(str(session.get('csrf_token','')),str(request.form.get('csrf_token',''))):
  abort(400,description='Invalid form token. Refresh the page and try again.')

def safe_next(target):
 if target and target.startswith('/') and not target.startswith('//') and not urlsplit(target).netloc: return target
 return url_for('account')

# OTP authentication: configure an SMS gateway before enabling production use.
# For local development only, codes are printed to the Flask server console.
_otp_limits={}
def _otp_error(message, status=400): return jsonify(ok=False,error=message),status
def _otp_key(phone): return hashlib.sha256((app.secret_key+phone).encode()).hexdigest()
def _phone(value):
 digits=re.sub(r'\D','',value or '')
 if len(digits)==10: digits='91'+digits
 return '+'+digits if len(digits)==12 and digits.startswith('91') and digits[2] in '6789' else None

@app.post('/auth/otp/send')
def otp_send():
 phone=_phone(request.form.get('phone')); mode=request.form.get('mode')
 if not phone or mode not in ('register','login'): return _otp_error('Enter a valid Indian mobile number.')
 init_db()
 with sqlite3.connect(DB) as con:
  con.row_factory=sqlite3.Row
  existing=con.execute('SELECT id FROM users WHERE phone=?',(phone,)).fetchone()
 if mode=='login' and not existing: return _otp_error('No account found for this mobile number. Please create an account.')
 if mode=='register' and existing: return _otp_error('This mobile number is already registered. Please sign in.')
 name=request.form.get('full_name','').strip();email=request.form.get('email','').strip().lower()
 if mode=='register':
  if not (2<=len(name)<=100 and len(email)<=254 and '@' in email and '.' in email.rsplit('@',1)[-1]): return _otp_error('Enter your name and a valid email address.')
  with sqlite3.connect(DB) as con:
   if con.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone(): return _otp_error('This email is already registered. Please sign in.')
 now=time.time(); key=_otp_key(phone); hits=[t for t in _otp_limits.get(key,[]) if now-t<3600]
 if len(hits)>=5: return _otp_error('Too many OTP requests. Try again later.',429)
 pending=session.get('otp_pending',{})
 if pending.get('sent_at',0)+30>now: return _otp_error('Please wait 30 seconds before requesting another code.',429)
 # Dummy OTP works ONLY on localhost. Production requires a real SMS provider.
 local_host=request.host.split(':')[0] in ('localhost','127.0.0.1','::1','[::1]')
 demo_mode=local_host and os.environ.get('OTP_DELIVERY','demo')=='demo'
 console_mode=local_host and os.environ.get('OTP_DELIVERY')=='console'
 if not (demo_mode or console_mode):
  return _otp_error('SMS delivery is not configured. Contact the site administrator.',503)
 code='123456' if demo_mode else f'{secrets.randbelow(1000000):06d}'
 session['otp_pending']=dict(phone=phone,mode=mode,name=name,email=email,digest=hmac.new(app.secret_key.encode(),code.encode(),hashlib.sha256).hexdigest(),sent_at=now,expires=now+300,attempts=0)
 _otp_limits[key]=hits+[now]
 app.logger.warning('LOCAL ONLY OTP for %s: %s (never use dummy OTP in production)',phone,code)
 return jsonify(ok=True,message='Demo OTP: 123456' if demo_mode else 'OTP generated: check the Flask terminal.',phone=phone)

@app.post('/auth/otp/verify')
def otp_verify():
 pending=session.get('otp_pending')
 if not pending: return _otp_error('Request a new OTP first.')
 now=time.time()
 if now>pending['expires']: session.pop('otp_pending',None);return _otp_error('OTP expired. Request a new code.')
 if pending['attempts']>=5: session.pop('otp_pending',None);return _otp_error('Too many incorrect attempts. Request a new OTP.',429)
 code=request.form.get('otp','')
 digest=hmac.new(app.secret_key.encode(),code.encode(),hashlib.sha256).hexdigest()
 if not (re.fullmatch(r'\d{6}',code) and hmac.compare_digest(digest,pending['digest'])):
  pending['attempts']+=1;session['otp_pending']=pending
  return _otp_error('Incorrect OTP. Please try again.')
 init_db()
 with sqlite3.connect(DB) as con:
  if pending['mode']=='register':
   try:
    cur=con.execute('INSERT INTO users(full_name,email,password_hash,phone,created_at) VALUES(?,?,?,?,?)',(pending['name'],pending['email'],'',pending['phone'],datetime.now().isoformat(timespec='seconds')))
    user_id=cur.lastrowid
   except sqlite3.IntegrityError: return _otp_error('An account with these details already exists.')
  else:
   row=con.execute('SELECT id FROM users WHERE phone=?',(pending['phone'],)).fetchone()
   if not row: return _otp_error('Account not found.')
   user_id=row[0]
 session.clear();session['user_id']=user_id;session['csrf_token']=secrets.token_urlsafe(32)
 return jsonify(ok=True,redirect=safe_next(request.form.get('next')))

@app.route('/register',methods=['GET'])
def register(): return redirect(url_for('home',auth='register'))

@app.route('/login',methods=['GET'])
def login():
 if g.user: return redirect(url_for('account'))
 return redirect(url_for('home',auth='login',next=request.args.get('next','')))

@app.get('/account')
def account():
 if not g.user: return redirect(url_for('login',next=request.path))
 init_db()
 with sqlite3.connect(DB) as con:
  con.row_factory=sqlite3.Row
  bookings=con.execute('SELECT * FROM booking_requests WHERE user_id=? ORDER BY created_at DESC',(g.user['id'],)).fetchall()
  orders=con.execute('SELECT * FROM booking_orders WHERE user_id=? ORDER BY created_at DESC',(g.user['id'],)).fetchall()
 items,total=cart_for(g.user['id'])
 return render_template('account.html',active='account',bookings=bookings,orders=orders,cart_items=items,cart_total=total,by_slug=BY_SLUG)

@app.post('/logout')
def logout():
 session.clear();flash('You have signed out.','success');return redirect(url_for('home'))


@app.get('/')
def home(): return render_template('home.html',active='home')

@app.get('/services')
def services():
 category=request.args.get('category','All Services'); q=request.args.get('q','').strip().lower()
 results=[s for s in SERVICES if (category=='All Services' or s['category']==category) and (not q or q in (s['name']+' '+s['short']).lower())]
 return render_template('services.html',active='services',results=results,category=category,q=q)

@app.get('/services/<slug>')
def detail(slug):
 s=BY_SLUG.get(slug)
 if not s: abort(404)
 return render_template('detail.html',active='services',s=s)

@app.route('/book',methods=['GET','POST'])
def book():
 if not g.user:
  next_url=url_for('book',service=request.values.get('service','ganapathi-homam'))
  return redirect(url_for('login',next=next_url))
 if request.method=='POST':
  f=request.form
  required=['service','preferred_date','preferred_time','district','venue','full_name','phone']
  if any(not f.get(k,'').strip() for k in required) or f.get('service') not in BY_SLUG or f.get('district') not in DISTRICTS:
   flash('Please complete the required booking details.');return redirect(url_for('book',service=f.get('service','ganapathi-homam')))
  try:
   if datetime.strptime(f['preferred_date'],'%Y-%m-%d').date() < datetime.now().date(): raise ValueError()
  except ValueError:
   flash('Please choose a valid future date.');return redirect(url_for('book',service=f['service']))
  ref='KP-'+uuid.uuid4().hex[:8].upper()
  init_db()
  with sqlite3.connect(DB) as con:
   con.execute('''INSERT INTO booking_requests (reference,created_at,service,preferred_date,preferred_time,district,venue,full_name,phone,email,address,notes,user_id,estimated_price) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(ref,datetime.now().isoformat(timespec='seconds'),f['service'],f['preferred_date'],f['preferred_time'],f['district'],f['venue'],f['full_name'].strip(),f['phone'].strip(),f.get('email','').strip(),f.get('address','').strip(),f.get('notes','').strip(),g.user['id'] if g.user else None,BY_SLUG[f['service']]['price']))
  return redirect(url_for('confirmation',ref=ref))
 s=BY_SLUG.get(request.args.get('service','ganapathi-homam'),SERVICES[0]);return render_template('book.html',active='book',s=s,today=datetime.now().strftime('%Y-%m-%d'))

@app.get('/confirmation/<ref>')
def confirmation(ref):
 init_db()
 with sqlite3.connect(DB) as con:
  con.row_factory=sqlite3.Row; row=con.execute('SELECT * FROM booking_requests WHERE reference=?',(ref,)).fetchone()
 if not row: abort(404)
 if row['user_id'] is not None and (not g.user or g.user['id']!=row['user_id']): abort(404)
 return render_template('confirmation.html',active='book',booking=row,s=BY_SLUG[row['service']])


@app.post('/cart/add/<slug>')
def cart_add(slug):
 if not g.user: return redirect(url_for('login',next=url_for('detail',slug=slug)))
 if slug not in BY_SLUG: abort(404)
 try: qty=int(request.form.get('quantity','1'))
 except ValueError: abort(400)
 if not 1<=qty<=20: abort(400)
 with sqlite3.connect(DB) as con:
  current=con.execute('SELECT quantity FROM cart_items WHERE user_id=? AND service_slug=?',(g.user['id'],slug)).fetchone()
  if current:
   con.execute('UPDATE cart_items SET quantity=? WHERE user_id=? AND service_slug=?',(min(20,current[0]+qty),g.user['id'],slug))
  else: con.execute('INSERT INTO cart_items(user_id,service_slug,quantity) VALUES(?,?,?)',(g.user['id'],slug,qty))
 flash('Added to your pooja cart.','success')
 return redirect(url_for('cart'))

@app.get('/cart')
def cart():
 if not g.user: return redirect(url_for('login',next=request.path))
 items,total=cart_for(g.user['id'])
 return render_template('cart.html',active='account',items=items,total=total)

@app.post('/cart/update/<int:item_id>')
def cart_update(item_id):
 if not g.user: return redirect(url_for('login'))
 try: qty=int(request.form.get('quantity','0'))
 except ValueError: abort(400)
 if not 0<=qty<=20: abort(400)
 with sqlite3.connect(DB) as con:
  if qty==0: con.execute('DELETE FROM cart_items WHERE id=? AND user_id=?',(item_id,g.user['id']))
  else: con.execute('UPDATE cart_items SET quantity=? WHERE id=? AND user_id=?',(qty,item_id,g.user['id']))
 return redirect(url_for('cart'))

@app.post('/cart/checkout')
def cart_checkout():
 if not g.user: return redirect(url_for('login'))
 init_db()
 with sqlite3.connect(DB) as con:
  con.execute('BEGIN IMMEDIATE')
  rows=con.execute('SELECT service_slug,quantity FROM cart_items WHERE user_id=?',(g.user['id'],)).fetchall()
  if not rows:
   flash('Your cart is empty.','error');return redirect(url_for('cart'))
  if any(slug not in BY_SLUG for slug,qty in rows): abort(400)
  total=sum(BY_SLUG[slug]['price']*qty for slug,qty in rows)
  ref='EP-'+uuid.uuid4().hex[:10].upper()
  con.execute('INSERT INTO booking_orders(id,user_id,created_at,total,status) VALUES(?,?,?,?,?)',(ref,g.user['id'],datetime.now().isoformat(timespec='seconds'),total,'Request received'))
  for slug,qty in rows:
   service=BY_SLUG[slug]
   con.execute('INSERT INTO order_items(order_id,service_slug,service_name,unit_price,quantity,line_total) VALUES(?,?,?,?,?,?)',(ref,slug,service['name'],service['price'],qty,service['price']*qty))
  con.execute('DELETE FROM cart_items WHERE user_id=?',(g.user['id'],))
 flash('Your bulk pooja request was saved. No payment was taken.','success')
 return redirect(url_for('invoice',order_id=ref))

@app.get('/invoice/<order_id>')
def invoice(order_id):
 if not g.user: return redirect(url_for('login',next=request.path))
 with sqlite3.connect(DB) as con:
  con.row_factory=sqlite3.Row
  order=con.execute('SELECT * FROM booking_orders WHERE id=? AND user_id=?',(order_id,g.user['id'])).fetchone()
  if not order: abort(404)
  lines=con.execute('SELECT * FROM order_items WHERE order_id=? ORDER BY id',(order_id,)).fetchall()
 return render_template('invoice.html',active='account',order=order,lines=lines)

@app.get('/how-it-works')
def how(): return render_template('how.html',active='how')

@app.get('/about')
def about(): return render_template('about.html',active='about')

@app.get('/priests')
def priests(): return render_template('priests.html',active='priests')

if __name__=='__main__':
 init_db();app.run(debug=os.environ.get('FLASK_DEBUG')=='1',port=int(os.environ.get('PORT','5000')))
