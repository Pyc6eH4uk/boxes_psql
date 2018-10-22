import os
import psycopg2
from flask import Flask, request, g, render_template, session, redirect, url_for
from utils.helper import colors

app = Flask('__name__')
app.secret_key = os.urandom(24)


def connect_db():
    return psycopg2.connect('postgres://postgres:user@localhost:5432/pyc6eh4uk')


@app.before_request
def before_request():
    g.db_conn = connect_db()


@app.route('/')
def index():
    if 'user' in session:
        cur = g.db_conn.cursor()
        cur.execute('SELECT box_name FROM boxes')
        boxes = cur.fetchall()
        return render_template('index.html', boxes=boxes)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        cur = g.db_conn.cursor()
        email = request.form['name']
        pwd = request.form['pwd']
        cur.execute('SELECT * FROM box_users WHERE user_login = %s AND user_password = %s', (email, pwd,))
        data = cur.fetchall()
        if not data:
            error = 'Login or password incorrect'
            return render_template('login.html', error=error)

        session['user'] = request.form['name']
        print(session)
        return redirect(url_for('available_boxes'))


@app.route('/boxes', methods=['GET', 'POST'])
def available_boxes():
    if request.method == 'GET':
        if 'user' in session:
            cur = g.db_conn.cursor()
            cur.execute('SELECT box_name, box_color FROM boxes')
            boxes = cur.fetchall()
            return render_template('boxes.html', boxes=boxes)
        else:
            return redirect(url_for('login'))

    if request.method == 'POST':
        if 'user' in session:
            name = request.form['name']
            color = request.form['color']
            cur = g.db_conn.cursor()
            cur.execute('SELECT user_id FROM box_users WHERE user_login = %s', (session['user'], ))
            user_id = cur.fetchone()[0]
            cur.execute('SELECT box_name FROM boxes')
            boxes = cur.fetchall()
            if color not in colors:
                error = 'You can not add box with such color: {}'.format(color)
                return render_template('boxes.html', boxes=boxes, error=error)
            cur.execute('SELECT box_color FROM boxes WHERE box_color = %s', (color, ))
            if cur.fetchall():
                error = 'You can not add box with such name: {}'.format(name)
                return render_template('boxes.html', boxes=boxes, error=error)
            cur.execute('SELECT * FROM boxes WHERE box_name = %s OR box_color = %s', (name, color, ))
            data = cur.fetchall()
            if not data:
                create_box(name, color, user_id)
                cur.execute('SELECT box_name, box_color FROM boxes')
                boxes = cur.fetchall()
                happy = 'We add your box to our storage.'
                return render_template('boxes.html', boxes=boxes, happy=happy)
            else:
                error = 'Box with such color or name already exist.'
                return render_template('boxes.html', boxes=boxes, error=error)
        else:
            return redirect(url_for('login'))


@app.route('/boxes/<box_name>', methods=['GET', 'PUT'])
def extend_box(box_name):
    if request.method == 'GET':
        if 'user' in session:
            if is_box_exist(box_name):
                cur = g.db_conn.cursor()
                cur.execute('SELECT box_color, box_id FROM boxes WHERE box_name = %s', (box_name, ))
                box_data = cur.fetchone()
                cur.execute('SELECT thing_name FROM box_things WHERE box_id = %s', (box_data[1], ))
                things = cur.fetchall()
                new_things = []
                for thing in things:
                    new_things.append(thing[0])
                new_things = sorted(new_things)
                cnt_things = []
                for thing in set(new_things):
                    cnt_things.append(new_things.count(thing))
                all_info = []
                for thing, cnt in zip(set(sorted(new_things)), cnt_things):
                    all_info.append([thing, cnt])
                return render_template('box_items.html', box_name=box_name,
                                       color=box_data[0],  things=sorted(all_info))

            else:
                return 'No boxes with {} name'.format(box_name), 404
        else:
            return redirect(url_for('login'))

    if request.method == 'PUT':
        if 'user' in session:
            if is_box_exist(box_name):
                cur = g.db_conn.cursor()
                cur.execute('SELECT user_id FROM box_users WHERE user_login = %s', (session['user'], ))
                creator = cur.fetchone()[0]
                cur.execute('SELECT box_name FROM boxes WHERE box_name = %s AND user_id = %s', (box_name, creator, ))
                if cur.fetchall():
                    name = request.form['name']
                    cur.execute('SELECT box_id FROM boxes WHERE box_name = %s', (box_name, ))
                    box_id = cur.fetchone()[0]
                    extend_boxes(name, box_id)
                    return redirect(url_for('extend_box', box_name=box_name))
                else:
                    error = 'Restricted access'
                    return render_template('box_items.html', error=error), 401
            else:
                return '<h1>No boxes with <b>{}</b> name<h1>'.format(box_name), 404
        else:
            return redirect(url_for('login'))


def is_box_exist(box_name):
    cur = g.db_conn.cursor()
    try:
        cur.execute('SELECT box_name FROM boxes WHERE box_name = %s', (box_name, ))
        cur.fetchone()[0]
    except:
        return False
    return True


def create_box(name, color, user_id):
    cur = g.db_conn.cursor()
    try:
        cur.execute('INSERT INTO boxes(box_name, box_color, user_id) VALUES(%s, %s, %s)', (name, color, user_id))
    except:
        pass
    g.db_conn.commit()


def extend_boxes(name, box_id):
    cur = g.db_conn.cursor()
    try:
        cur.execute('INSERT INTO box_things(thing_name, box_id) VALUES(%s, %s)', (name, box_id))
    except:
        pass
    g.db_conn.commit()


if __name__ == '__main__':
    app.run(debug=True)

