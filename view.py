from flask import render_template
import config

folder = config.view_folder

def store(items):
    return render_template('store.html', items=items)

def balance_box(balance):
    return render_template('balance_box.html', balance=balance)

def add_item():
    return render_template('add_item.html')