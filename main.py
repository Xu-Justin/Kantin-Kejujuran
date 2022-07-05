import os, shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy

import config, view, storage

app = Flask(__name__, template_folder=view.folder, static_folder=storage.folder)
app.config['SECRET_KEY'] = 'MLXH243GssUWwKdTWS7FDhdwYF56wPj8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + config.db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Integer)
    image_url = db.Column(db.String)
    timestamp = db.Column(db.TIMESTAMP)
    
    def __init__(self, name, description, price, image_url, timestamp):
        self.name = name
        self.description = description
        self.price = price
        self.image_url = image_url
        self.timestamp = timestamp
        
    def get(self):
        return self.id, self.name, self.description, self.price, self.image_url, self.timestamp
    
    def get_price_format(self):
        return f'Rp{self.price:,}'
    
class Balance(db.Model):
    __tablename__ = 'balances'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    
    def __init__(self, value):
        self.value = value
        
    def get_value_format(self):
        return f'Rp{self.value:,}'
    
def db_get_item(sort_by, order_type):
    comp = None
    
    if sort_by == 'name': comp = Item.name
    if sort_by == 'timestamp': comp = Item.timestamp
    
    if order_type == 'ascending' : comp = comp
    if order_type == 'descending': comp = comp.desc()
    
    return Item.query.order_by(comp).all()

def db_add_item(name, description, price, image_url, timestamp):
    record = Item(name, description, price, image_url, timestamp)
    db.session.add(record)
    db.session.commit()
    
def db_delete_item(id):
    record = Item.query.filter(Item.id == id).first()
    os.remove(record.image_url)
    db.session.delete(record)
    db.session.commit()

def db_empty_balance():
    records = Balance.query.all()
    if len(records): return False
    else: return True

def db_add_balance(value):
    record = Balance(value)
    db.session.add(record)
    db.session.commit()

def db_get_first_balance():
    record = Balance.query.first()
    return record

def db_first_balance_increase_value(value):
    record = Balance.query.first()
    record.value += value
    db.session.commit()

def db_first_balance_decrease_value(value):
    record = Balance.query.first()
    record.value -= value
    db.session.commit()

def get_timestamp():
    return db.func.current_timestamp()

@app.route("/store/<sort_by>/static/<path:path>")
def static_dir(sort_by, path):
    return send_from_directory(storage.folder, path)

@app.route('/', methods=['GET'])
@app.route('/store', methods=['GET'])
def store():
    messages = request.args
    return redirect(url_for('store_order', sort_by='timestamp', order_type='ascending', **messages))

@app.route('/store/<sort_by>/<order_type>', methods=['GET'])
def store_order(sort_by, order_type):
    items = db_get_item(sort_by, order_type)
    messages = request.args
    return view.store(items, sort_by, order_type, messages)

@app.route('/store/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'GET':
        messages = request.args
        return view.add_item(messages)
    
    elif request.method == 'POST':
        
        name = 'Super Long Item'
        description = '''Some quick example text to build on the card title and make up the bulk of the card's content.'''
        price = 0
        image = ''
        
        name = request.form.get('name', name)
        description = request.form.get('description', description)
        price = request.form.get('price', price)
        timestamp = get_timestamp()
        image = request.files.get('image', image)
        image_url = os.path.join(config.storage_folder, storage.get_unique_name(config.storage_folder, suffix=f'-{image.filename}', seed=timestamp))
        messages = dict()
        
        if not price.isdigit():
            messages['price_error'] = f'Price must be numeric.'
            return redirect(url_for('add_item', name=name, description=description, price=price, **messages))
            
        else:
            image.save(image_url)
            db_add_item(name, description, int(price), image_url, timestamp)
            messages['success'] = f'Added new item {name}.'        
            return redirect(url_for('store', **messages))
 
@app.route('/store/buy_item', methods=['POST'])
def buy_item():
    id = request.form.get('id', None)
    sort_by = request.form.get('sort_by', 'timestamp')
    order_type = request.form.get('order_type', 'descending')
    
    item = Item.query.filter(Item.id == id).first()
    db_first_balance_increase_value(item.price)
    db_delete_item(id)
    
    return redirect(url_for('store_order', sort_by=sort_by, order_type=order_type))    

@app.route('/balance_box', methods=['GET', 'POST'])
def balance_box():
    if request.method == 'GET':
        balance = db_get_first_balance()
        messages = request.args
        return view.balance_box(balance, messages)
    
    elif request.method == 'POST':
        
        value = 0
        action = 'add'
        
        value = request.form.get('value', value)
        action = request.form.get('action', action)
        messages = dict()
        
        if not value.isdigit():
            messages['value'] = value
            messages['value_error'] = f'Nominal must be numeric.'
        else:
            value = int(value)
            
            if action == 'add':
                if value > 0:
                    db_first_balance_increase_value(value)
                    messages['success'] = f'Successfully to add balance Rp{value:,}'
                else: messages['value_error'] = f'Nominal must be greater than zero.'
                
            elif action == 'withdraw':
                if value > 0 and value < db_get_first_balance().value:
                    db_first_balance_decrease_value(value)
                    messages['success'] = f'Successfully to withdraw balance Rp{value:,}'
                else: messages['value_error'] = f'Nominal must be greater than zero and less than {db_get_first_balance().value}'
        
        return redirect(url_for('balance_box', **messages))

def db_init(force=False):
    if force: os.remove(config.db_name)
    
    db.create_all()
    if db_empty_balance():
        db_add_balance(0)
        
        import time
        shutil.copyfile('./sample_images/tempe.jpg', os.path.join(storage.folder, 'tempe.jpg'))
        db_add_item('Tempe', 'Rasakan kenikmatan tempe yang tiada duanya. Dibuat dengan kacang kedelai asli dengan teknik fermentasi terbaik.', 7000, os.path.join(storage.folder, 'tempe.jpg'), get_timestamp())
        time.sleep(1)
        shutil.copyfile('./sample_images/tahu.jpg', os.path.join(storage.folder, 'tahu.jpg'))
        db_add_item('Tahu', 'Tahu enak, lembut, dan bergizi. Bagus untuk kesehatan dan cemilan. ENAK!', 6000, os.path.join(storage.folder, 'tahu.jpg'), get_timestamp())
        time.sleep(1)
        shutil.copyfile('./sample_images/bakwan.jpg', os.path.join(storage.folder, 'bakwan.jpg'))
        db_add_item('Bakwan', 'Terbuat dari sayur-sayuran asli, ada wortel, kol, dan lain-lain. Super murah!', 4000, os.path.join(storage.folder, 'bakwan.jpg'), get_timestamp())
        time.sleep(1)
        shutil.copyfile('./sample_images/ayam_goreng.jpg', os.path.join(storage.folder, 'ayam_goreng.jpg'))
        db_add_item('Ayam Goreng', 'Yam! yam! yam!', 50000, os.path.join(storage.folder, 'ayam_goreng.jpg'), get_timestamp())
        time.sleep(1)
        shutil.copyfile('./sample_images/mie_goreng.jpg', os.path.join(storage.folder, 'mie_goreng.jpg'))
        db_add_item('Mie Goreng', 'Siapa yang tidak suka mie goreng? super enak! garansi uang kembali.', 25000, os.path.join(storage.folder, 'mie_goreng.jpg'), get_timestamp())
        
if __name__ == '__main__':
    db_init(force=False)
    app.run(config.host, config.port, debug=False)