from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
import os
import datetime
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = "财务记录应用密钥"

# 确保数据库目录存在
db_dir = 'instance'
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
db_path = os.path.join(db_dir, 'finance.db')

# 数据库初始化
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 删除现有表（如果存在）
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS categories")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TEXT NOT NULL
    )
    ''')
    
    # 创建交易表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        type TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建分类表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, name)
    )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 用户密码哈希
def hash_password(password):
    """生成密码哈希值"""
    salt = hashlib.sha256(os.urandom(60)).hexdigest()
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = pwdhash.hex()
    return salt + pwdhash

def verify_password(stored_password, provided_password):
    """验证密码"""
    salt = stored_password[:64]
    stored_hash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = pwdhash.hex()
    return pwdhash == stored_hash

# 添加默认分类
def add_default_categories(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 预设一些基本分类
    default_expense_categories = ['餐饮', '交通', '购物', '住房', '娱乐', '医疗', '其他支出']
    default_income_categories = ['工资', '奖金', '投资收益', '其他收入']
    
    for category in default_expense_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (user_id, name, type) VALUES (?, ?, ?)", 
                      (user_id, category, '支出'))
    
    for category in default_income_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (user_id, name, type) VALUES (?, ?, ?)", 
                      (user_id, category, '收入'))
    
    conn.commit()
    conn.close()

# 登录验证装饰器
def login_required(route_function):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！', 'danger')
            return redirect(url_for('login'))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email') or None  # 如果为空字符串，设置为None
        
        # 表单验证
        if not username or not password or not confirm_password:
            flash('请填写所有必填字段！', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('两次输入的密码不匹配！', 'danger')
            return redirect(url_for('register'))
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            flash('用户名已存在！', 'danger')
            return redirect(url_for('register'))
        
        # 检查邮箱是否已存在
        if email:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                flash('邮箱已被注册！', 'danger')
                return redirect(url_for('register'))
        
        # 创建新用户
        hashed_password = hash_password(password)
        created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)",
            (username, hashed_password, email, created_at)
        )
        
        conn.commit()
        
        # 获取新用户ID
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        
        # 添加默认分类
        add_default_categories(user_id)
        
        conn.close()
        
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, password_hash, username FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user and verify_password(user[1], password):
            session['user_id'] = user[0]
            session['username'] = user[2]
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误！', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('您已成功退出登录！', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取最近的交易记录
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 10", (user_id,))
    transactions = cursor.fetchall()
    
    # 获取收入和支出总额
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = '收入'", (user_id,))
    total_income = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = '支出'", (user_id,))
    total_expense = cursor.fetchone()[0] or 0
    
    balance = total_income - total_expense
    
    # 获取所有分类
    cursor.execute("SELECT * FROM categories WHERE user_id = ?", (user_id,))
    categories = cursor.fetchall()
    
    conn.close()
    
    # 添加今天的日期，用于表单默认值
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    return render_template('index.html', 
                          transactions=transactions, 
                          total_income=total_income, 
                          total_expense=total_expense, 
                          balance=balance,
                          categories=categories,
                          today=today)

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    user_id = session.get('user_id')
    date = request.form.get('date')
    category = request.form.get('category')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    type = request.form.get('type')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO transactions (user_id, date, category, amount, description, type) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, date, category, amount, description, type)
    )
    
    conn.commit()
    conn.close()
    
    flash('交易记录已添加成功！', 'success')
    return redirect(url_for('index'))

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    user_id = session.get('user_id')
    name = request.form.get('name')
    type = request.form.get('type')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO categories (user_id, name, type) VALUES (?, ?, ?)",
            (user_id, name, type)
        )
        conn.commit()
        flash('分类已添加成功！', 'success')
    except sqlite3.IntegrityError:
        flash('该分类已存在！', 'danger')
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/stats')
@login_required
def stats():
    user_id = session.get('user_id')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 按月统计
    cursor.execute("""
    SELECT strftime('%Y-%m', date) as month, 
           SUM(CASE WHEN type = '收入' THEN amount ELSE 0 END) as income,
           SUM(CASE WHEN type = '支出' THEN amount ELSE 0 END) as expense
    FROM transactions 
    WHERE user_id = ?
    GROUP BY month 
    ORDER BY month DESC
    """, (user_id,))
    monthly_stats = cursor.fetchall()
    
    # 按类别统计支出
    cursor.execute("""
    SELECT category, SUM(amount) as total
    FROM transactions 
    WHERE user_id = ? AND type = '支出'
    GROUP BY category 
    ORDER BY total DESC
    """, (user_id,))
    expense_by_category = cursor.fetchall()
    
    # 按类别统计收入
    cursor.execute("""
    SELECT category, SUM(amount) as total
    FROM transactions 
    WHERE user_id = ? AND type = '收入'
    GROUP BY category 
    ORDER BY total DESC
    """, (user_id,))
    income_by_category = cursor.fetchall()
    
    conn.close()
    
    return render_template('stats.html', 
                          monthly_stats=monthly_stats,
                          expense_by_category=expense_by_category,
                          income_by_category=income_by_category)

@app.route('/delete_transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    user_id = session.get('user_id')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 首先检查记录是否属于当前用户
    cursor.execute("SELECT user_id FROM transactions WHERE id = ?", (id,))
    record = cursor.fetchone()
    
    if not record or record[0] != user_id:
        conn.close()
        flash('无权删除此记录！', 'danger')
        return redirect(url_for('index'))
    
    cursor.execute("DELETE FROM transactions WHERE id = ?", (id,))
    
    conn.commit()
    conn.close()
    
    flash('交易记录已删除！', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 
