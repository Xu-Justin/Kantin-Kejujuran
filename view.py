from flask import render_template
import config

folder = config.view_folder

def store(items, sort_by, order_type, messages=dict()):
    return render_template('store.html', items=items, sort_by=sort_by, order_type=order_type, **messages)

def balance_box(balance, messages=dict()):
    return render_template('balance_box.html', balance=balance, **messages)

def add_item(messages=dict()):
    return render_template('add_item.html', **messages)