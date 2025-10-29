# lunashop.py
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g
import sqlite3, hashlib, os
from datetime import datetime

# ---------------- CONFIG ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey_v3_college"
DB = "ecommerce.db"
PER_PAGE = 8

# ---------------- DB ----------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db: db.close()

# ---------------- HELPERS ----------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def paginate(query, params, page, per_page=PER_PAGE):
    offset = (page-1)*per_page
    db = get_db()
    rows = db.execute(query + " LIMIT ? OFFSET ?", params + (per_page, offset)).fetchall()
    return rows

def site_base(title, body_html):
    """Bootstrap 5 light theme header/footer — used for all pages (single-file HTML)."""
    user_part = ""
    if session.get('user_id'):
        user_part = f"""
            <span class="me-3">Hello, <strong>{session.get('username')}</strong></span>
            <a class="btn btn-sm btn-outline-light me-2" href="{url_for('cart')}">🛒 Cart</a>
            <a class="btn btn-sm btn-outline-light" href="{url_for('logout')}">Logout</a>
        """
    else:
        user_part = f"""
            <a class="btn btn-sm btn-outline-light me-2" href="{url_for('login')}">Login</a>
            <a class="btn btn-sm btn-outline-light" href="{url_for('register')}">Register</a>
        """

    # fetch categories for header
    try:
        db = get_db()
        cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    except:
        cats = []

    cats_html = "".join([f'<a class="nav-link" href="{url_for("category", id=c["category_id"])}">{c["name"]}</a>' for c in cats])

    template = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background:#f5f6f8; }}
            .card-hover:hover {{ transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); }}
            .product-img {{ height: 180px; object-fit: cover; background: #f2f3f6; border-radius: .375rem; }}
            header .nav-link {{ color: #222; }}
            .search-input {{ width: 420px; max-width: 45vw; }}
            footer {{ background:#111; color:#ddd; padding: 14px 0; margin-top: 36px; }}
        </style>
      </head>
      <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
          <div class="container">
            <a class="navbar-brand text-primary fw-bold" href="{url_for('index')}">LunaShop</a>
            <form class="d-flex mx-3" action="{url_for('index')}" method="get">
                <input class="form-control form-control-sm search-input" type="search" placeholder="Search products..." aria-label="Search" name="q" value="{request.args.get('q','')}">
                <button class="btn btn-sm btn-primary ms-2" type="submit">Search</button>
            </form>

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarsExample">
              <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarsExample">
              <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item"><a class="nav-link" href="{url_for('index')}">Home</a></li>
                <li class="nav-item dropdown">
                  <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">Categories</a>
                  <ul class="dropdown-menu">
                    {''.join([f'<li><a class="dropdown-item" href="{url_for("category", id=c["category_id"])}">{c["name"]}</a></li>' for c in cats])}
                  </ul>
                </li>
                <li class="nav-item"><a class="nav-link" href="{url_for('orders')}">Orders</a></li>
              </ul>

              <div class="d-flex align-items-center">
                {user_part}
              </div>
            </div>
          </div>
        </nav>

        <main class="container mt-4">
            {body_html}
        </main>

        <footer class="text-center">
          <div class="container">
            <small>© 2025 LunaShop — College Project</small>
          </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
      </body>
    </html>
    """
    return template

# ---------------- AUTH ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        pw = request.form.get('password','')
        if not username or not email or not pw:
            flash("All fields required","danger")
            return redirect(url_for('register'))
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,email,password,is_admin) VALUES (?,?,?,0)", (username, email, hash_pw(pw)))
            conn.commit()
            flash("Account created. Please login.","success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered.","danger")
            return redirect(url_for('register'))

    html = """
      <div class="row justify-content-center">
        <div class="col-md-6">
          <div class="card p-4">
            <h4>Register</h4>
            <form method="post">
              <div class="mb-2">
                <label class="form-label">Username</label>
                <input class="form-control" name="username" required>
              </div>
              <div class="mb-2">
                <label class="form-label">Email</label>
                <input class="form-control" type="email" name="email" required>
              </div>
              <div class="mb-3">
                <label class="form-label">Password</label>
                <input class="form-control" type="password" name="password" required>
              </div>
              <button class="btn btn-primary">Create account</button>
            </form>
          </div>
        </div>
      </div>
    """
    return render_template_string(site_base("Register", html))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form.get('email','').strip()
        pw = request.form.get('password','')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hash_pw(pw))).fetchone()
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            flash("Logged in","success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials","danger")
            return redirect(url_for('login'))

    html = """
      <div class="row justify-content-center">
        <div class="col-md-5">
          <div class="card p-4">
            <h4>Login</h4>
            <form method="post">
              <div class="mb-2">
                <label class="form-label">Email</label>
                <input class="form-control" name="email" type="email" required>
              </div>
              <div class="mb-3">
                <label class="form-label">Password</label>
                <input class="form-control" name="password" type="password" required>
              </div>
              <button class="btn btn-primary">Login</button>
            </form>
          </div>
        </div>
      </div>
    """
    return render_template_string(site_base("Login", html))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out","info")
    return redirect(url_for('index'))

# ---------------- PRODUCT LIST / SEARCH ----------------
@app.route('/')
def index():
    q = request.args.get('q','').strip()
    page = int(request.args.get('page',1))
    db = get_db()

    params = tuple()
    if q:
        like = f"%{q}%"
        total = db.execute("SELECT COUNT(*) as c FROM products WHERE name LIKE ? OR description LIKE ?", (like, like)).fetchone()['c']
        products = paginate("SELECT * FROM products WHERE name LIKE ? OR description LIKE ? ORDER BY product_id DESC", (like, like), page)
        title = f"Search: {q}"
    else:
        total = db.execute("SELECT COUNT(*) as c FROM products").fetchone()['c']
        products = paginate("SELECT * FROM products ORDER BY product_id DESC", (), page)
        title = "Featured Products"

    total_pages = max(1, (total + PER_PAGE -1)//PER_PAGE)

    cards = ""
    for p in products:
        img_html = ""
        if p['image']:
            img_html = f'<img src="/static/images/{p["image"]}" class="product-img w-100 mb-2" alt="{p["name"]}">'
        cards += f"""
            <div class="col-md-3">
              <div class="card card-hover p-3">
                {img_html}
                <h6><a href="{url_for('product', id=p['product_id'])}" class="text-decoration-none">{p['name']}</a></h6>
                <p class="text-muted small">{(p['description'] or '')[:90]}</p>
                <div class="d-flex justify-content-between align-items-center mt-2">
                    <div class="fw-bold text-primary">₹{p['price']:.2f}</div>
                    <div>
                        <a href="{url_for('product', id=p['product_id'])}" class="btn btn-sm btn-outline-secondary me-1">View</a>
                        <a href="{url_for('add_to_cart', id=p['product_id'])}" class="btn btn-sm btn-success">Add to Cart</a>
                    </div>
                </div>
              </div>
            </div>
        """

    pagination_html = f"""
      <nav aria-label="page-nav">
        <ul class="pagination">
          <li class="page-item {'disabled' if page<=1 else ''}">
            <a class="page-link" href="{url_for('index')}?page={page-1}&q={q}">Previous</a>
          </li>
          <li class="page-item disabled"><span class="page-link">Page {page}/{total_pages}</span></li>
          <li class="page-item {'disabled' if page>=total_pages else ''}">
            <a class="page-link" href="{url_for('index')}?page={page+1}&q={q}">Next</a>
          </li>
        </ul>
      </nav>
    """

    html = f"""
      <div class="mb-3">
        <h2>{title}</h2>
      </div>
      <div class="row g-3">
        {cards or '<div class="col-12"><div class="alert alert-light">No products found.</div></div>'}
      </div>
      <div class="mt-4">{pagination_html}</div>
    """
    return render_template_string(site_base("Home", html))

@app.route('/category/<int:id>')
def category(id):
    page = int(request.args.get('page',1))
    db = get_db()
    cat = db.execute("SELECT * FROM categories WHERE category_id=?", (id,)).fetchone()
    if not cat:
        return render_template_string(site_base("Category", "<h3>Category not found</h3>"))
    total = db.execute("SELECT COUNT(*) as c FROM products WHERE category_id=?", (id,)).fetchone()['c']
    products = paginate("SELECT * FROM products WHERE category_id=? ORDER BY product_id DESC", (id,), page)
    cards = ""
    for p in products:
        cards += f"""
            <div class="col-md-3">
              <div class="card p-3 card-hover">
                <h6><a href="{url_for('product', id=p['product_id'])}">{p['name']}</a></h6>
                <p class="text-muted small">{(p['description'] or '')[:80]}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <div class="fw-bold text-primary">₹{p['price']:.2f}</div>
                    <a class="btn btn-sm btn-success" href="{url_for('add_to_cart', id=p['product_id'])}">Add</a>
                </div>
              </div>
            </div>
        """
    html = f"""
      <h2>Category: {cat['name']}</h2>
      <div class="row g-3">{cards or '<div class="col-12 alert alert-light">No products</div>'}</div>
    """
    return render_template_string(site_base(cat['name'], html))

@app.route('/product/<int:id>')
def product(id):
    db = get_db()
    p = db.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id=c.category_id WHERE product_id=?", (id,)).fetchone()
    if not p:
        return render_template_string(site_base("Product", "<h3>Product not found</h3>"))
    img_html = f'<img src="/static/images/{p["image"]}" class="product-img mb-3 w-100">' if p['image'] else ''
    html = f"""
      <div class="row">
        <div class="col-md-5">
          {img_html}
        </div>
        <div class="col-md-7">
          <h2>{p['name']}</h2>
          <p class="text-muted">Category: {p['category_name'] or 'Uncategorized'}</p>
          <p>{p['description'] or ''}</p>
          <h4 class="text-primary">₹{p['price']:.2f}</h4>
          <a class="btn btn-success me-2" href="{url_for('add_to_cart', id=p['product_id'])}">Add to Cart</a>
          <a class="btn btn-outline-secondary" href="{url_for('index')}">Back</a>
        </div>
      </div>
    """
    return render_template_string(site_base(p['name'], html))

# ---------------- CART & CHECKOUT ----------------
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'user_id' not in session:
        flash("Please login first","warning")
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    cart.append(id)
    session['cart'] = cart
    flash("Added to cart","success")
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    if not cart:
        return render_template_string(site_base("Cart", "<h3>Your cart is empty.</h3>"))
    db = get_db()
    placeholders = ",".join("?"*len(cart))
    products = db.execute(f"SELECT * FROM products WHERE product_id IN ({placeholders})", tuple(cart)).fetchall()
    total = sum([p['price'] for p in products])
    rows = ""
    # count quantities
    qty = {}
    for pid in cart: qty[pid] = qty.get(pid,0)+1
    for p in products:
        q = qty.get(p['product_id'],1)
        rows += f"""
            <div class="card mb-2 p-3 d-flex justify-content-between align-items-center">
              <div>
                <h6>{p['name']}</h6>
                <div class="text-muted small">{(p['description'] or '')[:80]}</div>
              </div>
              <div class="text-end">
                <div class="fw-bold">₹{p['price']:.2f} x {q}</div>
                <a href="{url_for('remove_from_cart', id=p['product_id'])}" class="btn btn-sm btn-outline-danger mt-2">Remove</a>
              </div>
            </div>
        """
    html = f"""
      <h3>Your Cart</h3>
      {rows}
      <div class="d-flex justify-content-between align-items-center mt-3">
        <div><strong>Total:</strong> ₹{total:.2f}</div>
        <div>
          <a class="btn btn-secondary" href="{url_for('index')}">Continue Shopping</a>
          <a class="btn btn-primary" href="{url_for('checkout')}">Checkout</a>
        </div>
      </div>
    """
    return render_template_string(site_base("Cart", html))

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    cart = session.get('cart', [])
    new = [x for x in cart if x!=id]
    session['cart'] = new
    flash("Removed from cart","info")
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if 'user_id' not in session:
        flash("Please login to checkout","warning")
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    if not cart:
        flash("Cart empty","warning")
        return redirect(url_for('index'))
    db = get_db()
    placeholders = ",".join("?"*len(cart))
    prods = db.execute(f"SELECT * FROM products WHERE product_id IN ({placeholders})", tuple(cart)).fetchall()
    total = sum([p['price'] for p in prods])

    if request.method=='POST':
        payment_mode = request.form.get('payment_mode')
        payment_info = ''
        if payment_mode == 'card':
            # minimal mock validation
            card_no = request.form.get('card_no','').strip()
            name = request.form.get('card_name','').strip()
            if len(card_no) < 12:
                flash("Enter a valid fake card number (12+ digits).","danger")
                return redirect(url_for('checkout'))
            payment_info = f"Card ending {card_no[-4:]} ({name})"
        elif payment_mode == 'upi':
            upi = request.form.get('upi_id','').strip()
            if '@' not in upi:
                flash("Enter a fake UPI like 'demo@upi'","danger")
                return redirect(url_for('checkout'))
            payment_info = f"UPI {upi}"
        else:
            payment_info = "Cash on Delivery"

        # create order
        cur = db.cursor()
        status = f"Placed - {payment_mode.upper()}"
        cur.execute("INSERT INTO orders (user_id,total_amount,status) VALUES (?,?,?)", (session['user_id'], total, status))
        order_id = cur.lastrowid
        # build qty map
        qty={}
        for pid in cart: qty[pid]=qty.get(pid,0)+1
        for p in prods:
            q = qty.get(p['product_id'],1)
            cur.execute("INSERT INTO order_items (order_id,product_id,quantity,price) VALUES (?,?,?,?)", (order_id, p['product_id'], q, p['price']))
        db.commit()
        # clear cart
        session.pop('cart', None)

        # show confirmation
        conf_html = f"""
          <div class="card p-4">
            <h3 class="text-success">Order Placed Successfully ✅</h3>
            <p>Order ID: <strong>#{order_id}</strong></p>
            <p>Total Paid: <strong>₹{total:.2f}</strong></p>
            <p>Payment Method: <strong>{payment_mode.upper()}</strong></p>
            <p>Payment Info: <strong>{payment_info}</strong></p>
            <a class="btn btn-primary mt-3" href="{url_for('orders')}">View My Orders</a>
            <a class="btn btn-outline-secondary mt-3 ms-2" href="{url_for('index')}">Continue Shopping</a>
          </div>
        """
        return render_template_string(site_base("Order Placed", conf_html))

    # GET -> render payment options form
    form_html = f"""
      <div class="row">
        <div class="col-md-7">
          <div class="card p-3">
            <h4>Choose Payment Method</h4>
            <form method="post">
              <div class="mb-3">
                <label class="form-label">Select</label>
                <select id="paymode" name="payment_mode" class="form-select" required onchange="toggleFields()">
                  <option value="cod">Cash on Delivery</option>
                  <option value="upi">UPI</option>
                  <option value="card">Card</option>
                </select>
              </div>

              <div id="upi_fields" style="display:none;">
                <div class="mb-2">
                  <label class="form-label">UPI ID (fake ok)</label>
                  <input class="form-control" name="upi_id" placeholder="demo@upi">
                </div>
              </div>

              <div id="card_fields" style="display:none;">
                <div class="mb-2"><label class="form-label">Card Number (fake)</label><input class="form-control" name="card_no" placeholder="411111111111"></div>
                <div class="mb-2"><label class="form-label">Name on Card</label><input class="form-control" name="card_name" placeholder="Full Name"></div>
                <div class="row">
                  <div class="col"><input class="form-control" name="card_exp" placeholder="MM/YY"></div>
                  <div class="col"><input class="form-control" name="card_cvv" placeholder="CVV"></div>
                </div>
              </div>

              <div class="mt-3">
                <button class="btn btn-success">Place Order</button>
                <a class="btn btn-outline-secondary ms-2" href="{url_for('cart')}">Back to Cart</a>
              </div>
            </form>
          </div>
        </div>

        <div class="col-md-5">
          <div class="card p-3">
            <h5>Order Summary</h5>
            <hr>
            {"".join([f"<div class='d-flex justify-content-between'><div>{p['name']}</div><div>₹{p['price']:.2f}</div></div>" for p in prods])}
            <hr>
            <div class="d-flex justify-content-between fw-bold">Total <div>₹{total:.2f}</div></div>
          </div>
        </div>
      </div>

      <script>
        function toggleFields(){{
          var v=document.getElementById('paymode').value;
          document.getElementById('upi_fields').style.display = v=='upi' ? 'block' : 'none';
          document.getElementById('card_fields').style.display = v=='card' ? 'block' : 'none';
        }}
        // init
        toggleFields();
      </script>
    """
    return render_template_string(site_base("Checkout", form_html))

# ---------------- ORDERS ----------------
@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash("Please login to view orders","warning")
        return redirect(url_for('login'))
    db = get_db()
    rows = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    if not rows:
        html = "<h3>No orders yet</h3>"
        return render_template_string(site_base("Orders", html))
    out = ""
    for o in rows:
        items = db.execute("SELECT oi.*, p.name FROM order_items oi LEFT JOIN products p ON p.product_id=oi.product_id WHERE oi.order_id=?", (o['order_id'],)).fetchall()
        items_html = "".join([f"<li>{it['name']} x{it['quantity']} - ₹{it['price']:.2f}</li>" for it in items])
        out += f"""
          <div class="card mb-3 p-3">
            <div class="d-flex justify-content-between">
              <div>
                <h6>Order #{o['order_id']}</h6>
                <div class="small text-muted">Placed: {o['created_at']}</div>
                <div class="mt-2"><strong>Status:</strong> {o['status']}</div>
              </div>
              <div class="text-end">
                <div class="fw-bold">₹{o['total_amount']:.2f}</div>
              </div>
            </div>
            <hr>
            <ul class="mb-0">{items_html}</ul>
          </div>
        """
    return render_template_string(site_base("My Orders", out))

# ---------------- RUN ----------------
if __name__ == "__main__":
    if not os.path.exists(DB):
        print("Database not found. Create it from schema.sql or place ecommerce.db in this folder.")
    app.run(debug=True)
