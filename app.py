import os
import psycopg2
from flask import Flask, request, g, render_template, session, redirect, url_for
from utils.helper import colors

app = Flask('__name__')
app.secret_key = os.urandom(24)


def connect_db():
    return psycopg2.connect('postgres://postgres:user@localhost:5432/postgres')


@app.before_request
def before_request():
    g.db_conn = connect_db()


@app.route('/')
def index():
    print('here')
    if 'user' in session:
        cur = g.db_conn.cursor()
        cur.execute('SELECT box_name FROM boxes')
        boxes = cur.fetchall()
        return str(boxes)
        # return render_template('index.html', boxes=boxes)
    else:
        # return render_template('login.html')
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
            return render_template('login.html')

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
            print(user_id)
            cur.execute('SELECT box_name FROM boxes')
            boxes = cur.fetchall()
            print(boxes)
            if color not in colors:
                error = 'You can not add box with such color: {}'.format(color)
                return error
                # return render_template('boxes.html', boxes=boxes, error=error)
            cur.execute('SELECT box_color FROM boxes WHERE box_color = %s', (color, ))
            if cur.fetchall():
               return 'Takoi est'
            cur.execute('SELECT * FROM boxes WHERE box_name = %s OR box_color = %s', (name, color, ))
            data = cur.fetchall()
            if not data:
                print('create')
                create_box(name, color, user_id)
                cur.execute('SELECT box_name, box_color FROM boxes')
                boxes = cur.fetchall()
                print(boxes)
                happy = 'We add your box to our storage.'
                return render_template('boxes.html', boxes=boxes, happy=happy)

            # if color not in boxes.values() and name not in boxes.keys():
            #     create_box(name, color)
            #     happy = 'We add your box to our storage.'
            #     return render_template('boxes.html', boxes=boxes, happy=happy)
            else:
                print('not_create')
                error = 'Box with such color or name already exist.'
                return render_template('boxes.html', boxes=boxes, error=error)
        else:
            return redirect(url_for('login'))


@app.route('/boxes/<box_name>', methods=['GET', 'PUT'])
def extend_box(box_name):
    if request.method == 'GET':
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

    if request.method == 'PUT':
        if is_box_exist(box_name):
            cur = g.db_conn.cursor()
            cur.execute('SELECT user_id FROM box_users WHERE user_login = %s', (session['user'], ))
            creator = cur.fetchone()[0]
            cur.execute('SELECT box_name FROM boxes WHERE box_name = %s AND user_id = %s', (box_name, creator, ))
            # if session['user'] == creator:
            if cur.fetchall():
                name = request.form['name']
                cur.execute('SELECT box_id FROM boxes WHERE box_name = %s', (box_name, ))
                box_id = cur.fetchone()[0]
                extend_boxes(name, box_id)
                cur.execute('SELECT thing_name FROM box_things WHERE box_id = %s', (box_id,))
                things = cur.fetchall()
                cur.execute('SELECT box_color FROM boxes WHERE box_name = %s', (box_name,))
                color = cur.fetchone()[0]
                return redirect(url_for('extend_box', box_name=box_name))
            else:
                return 'Restricted access', 400
        else:
            return 'No boxes with {} name'.format(box_name), 404


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