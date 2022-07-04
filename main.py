import os
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
        
def db_get_item(order='name'):
    if order == 'name': return Item.query.order_by(Item.name).all()
    if order == 'timestamp': return Item.query.order_by(Item.timestamp).all()

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

@app.route('/store', methods=['GET'])
def store():
    return redirect(url_for('store_order', order='name'))

@app.route("/store/static/<path:path>")
def static_dir(path):
    return send_from_directory(storage.folder, path)

@app.route('/store/<order>', methods=['GET'])
def store_order(order):
    items = db_get_item(order)
    return view.store(items)

@app.route('/store/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'GET':
        return view.add_item()
    
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
        image.save(image_url)
        
        db_add_item(name, description, int(price), image_url, timestamp)
        return redirect(url_for('store'))

@app.route('/store/delete_item', methods=['POST'])
def delete_item():
    id = request.form.get('id', None)
    
    db_delete_item(id)
    return redirect(url_for('store'))    

@app.route('/balance_box', methods=['GET', 'POST'])
def balance_box():
    if request.method == 'GET':
        balance = db_get_first_balance()
        return view.balance_box(balance)
    
    elif request.method == 'POST':
        
        value = 0
        action = 'add'
        
        value = request.form.get('value', value)
        action = request.form.get('action', action)
        
        value = int(value)
        
        if action == 'add': db_first_balance_increase_value(value)
        elif action == 'withdraw': db_first_balance_decrease_value(value)
        
        return redirect(url_for('balance_box'))

def db_init():
    db.create_all()
    if db_empty_balance(): db_add_balance(0)

if __name__ == '__main__':
    db_init()
    app.run(config.host, config.port, debug=True)