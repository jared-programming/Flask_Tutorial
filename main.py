from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
import math

app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/boatsdb"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


# render a file
@app.route('/')
def index():
    return render_template('index.html')


# remember how to take user inputs?
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# get all boats
# this is done to handle requests for two routes -
@app.route('/boats/')
@app.route('/boats/<page>')
def get_boats(page=1):
    page = int(request.args.get('page', page))  # allow page in query
    if page < 1:
        page = 1
    per_page = 15  # records to show per page
    
    # Get filters
    q = request.args.get('q')
    type_filter = request.args.get('type')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    sort = request.args.get('sort', 'id')
    
    # Validate sort parameter
    valid_sorts = {'id': 'id', 'name': 'name', 'price': 'rental_price', 'owner_id': 'owner_id'}
    sort_column = valid_sorts.get(sort, 'id')
    
    # Get distinct types for dropdown
    types_result = conn.execute(text("SELECT DISTINCT type FROM boats")).all()
    types = [row[0] for row in types_result]
    
    # Build query
    base_query = "SELECT * FROM boats"
    count_query = "SELECT COUNT(*) FROM boats"
    conditions = []
    params = {}
    
    if q:
        conditions.append("(LOWER(name) LIKE LOWER(:q) OR CAST(id AS CHAR) = :q_exact OR LOWER(type) LIKE LOWER(:q) OR CAST(owner_id AS CHAR) = :q_exact)")
        params['q'] = f"%{q}%"
        params['q_exact'] = q
    if type_filter:
        conditions.append("type = :type")
        params['type'] = type_filter
    if min_price:
        conditions.append("rental_price >= :min_price")
        params['min_price'] = float(min_price)
    if max_price:
        conditions.append("rental_price <= :max_price")
        params['max_price'] = float(max_price)
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    order_clause = f" ORDER BY {sort_column}"
    base_query += where_clause + order_clause
    count_query += where_clause
    
    total = conn.execute(text(count_query), params).scalar()
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    boats = conn.execute(text(f"{base_query} LIMIT {per_page} OFFSET {(page - 1) * per_page}"), params).all()
    print(boats)
    return render_template('boats.html', boats=boats, page=page, per_page=per_page, total_pages=total_pages, q=q, type=type_filter, min_price=min_price, max_price=max_price, types=types, sort=sort)


@app.route('/create', methods=['GET'])
def create_get_request():
    return render_template('boats_create.html')


@app.route('/create', methods=['POST'])
def create_boat():
    # you can access the values with request.from.name
    # this name is the value of the name attribute in HTML form's input element
    # ex: print(request.form['id'])
    try:
        conn.execute(
            text("INSERT INTO boats values (:id, :name, :type, :owner_id, :rental_price)"),
            request.form
        )
        return render_template('boats_create.html', error=None, success="Data inserted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_create.html', error=error, success=None)


@app.route('/delete', methods=['GET'])
def delete_get_request():
    return render_template('boats_delete.html')


@app.route('/delete', methods=['POST'])
def delete_boat():
    try:
        conn.execute(
            text("DELETE FROM boats WHERE id = :id"),
            request.form
        )
        return render_template('boats_delete.html', error=None, success="Data deleted successfully!")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('boats_delete.html', error=error, success=None)


if __name__ == '__main__':
    app.run(debug=True)
