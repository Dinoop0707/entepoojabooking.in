"""Kerala pooja booking concept - local Flask demo. No live priest availability or payments."""
import os, sqlite3, uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, abort

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'local-preview-change-before-production')
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
  con.execute('''CREATE TABLE IF NOT EXISTS booking_requests (reference TEXT PRIMARY KEY, created_at TEXT NOT NULL, service TEXT NOT NULL, preferred_date TEXT NOT NULL, preferred_time TEXT NOT NULL, district TEXT NOT NULL, venue TEXT NOT NULL, full_name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT, address TEXT, notes TEXT)''')

@app.context_processor
def common(): return dict(districts=DISTRICTS,services=SERVICES,year=datetime.now().year)

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
   con.execute('INSERT INTO booking_requests VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(ref,datetime.now().isoformat(timespec='seconds'),f['service'],f['preferred_date'],f['preferred_time'],f['district'],f['venue'],f['full_name'].strip(),f['phone'].strip(),f.get('email','').strip(),f.get('address','').strip(),f.get('notes','').strip()))
  return redirect(url_for('confirmation',ref=ref))
 s=BY_SLUG.get(request.args.get('service','ganapathi-homam'),SERVICES[0]);return render_template('book.html',active='book',s=s,today=datetime.now().strftime('%Y-%m-%d'))

@app.get('/confirmation/<ref>')
def confirmation(ref):
 init_db()
 with sqlite3.connect(DB) as con:
  con.row_factory=sqlite3.Row; row=con.execute('SELECT * FROM booking_requests WHERE reference=?',(ref,)).fetchone()
 if not row: abort(404)
 return render_template('confirmation.html',active='book',booking=row,s=BY_SLUG[row['service']])

@app.get('/how-it-works')
def how(): return render_template('how.html',active='how')

@app.get('/about')
def about(): return render_template('about.html',active='about')

@app.get('/priests')
def priests(): return render_template('priests.html',active='priests')

if __name__=='__main__':
 init_db();app.run(debug=os.environ.get('FLASK_DEBUG')=='1',port=int(os.environ.get('PORT','5000')))
