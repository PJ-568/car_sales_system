import argparse
import os
import http.server
import json
import socketserver
import sqlite3
from urllib.parse import urlparse, parse_qs

# 初始化数据库结构
def initialize_database():
    # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
    conn, cursor = connect_to_database()

    # 创建表结构
    # 车辆信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            manufacturer_id INTEGER,
            FOREIGN KEY (manufacturer_id) REFERENCES manufacturers(id)
        )
    ''')

    # 厂商信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manufacturers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')

    # 操作员信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 客户信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_info TEXT
        )
    ''')

    # 财务信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financials (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER,
            transaction_type TEXT NOT NULL,
            amount INTEGER,
            customer_id INTEGER,
            date TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    # 库存信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    ''')

    # 提交事务
    conn.commit()
    # 关闭连接
    conn.close()

# 初始化数据库内容
def initialize_data():
    # 连接到 SQLite 数据库
    conn, cursor = connect_to_database()
    
    # 插入厂商信息
    cursor.execute("INSERT INTO manufacturers (name) VALUES ('宝马')")
    cursor.execute("INSERT INTO manufacturers (name) VALUES ('奥迪')")
    cursor.execute("INSERT INTO manufacturers (name) VALUES ('梅赛德斯')")

    # 插入车辆信息
    cursor.execute("INSERT INTO vehicles (brand, model, manufacturer_id) VALUES ('宝马', 'X5', 1)")
    cursor.execute("INSERT INTO vehicles (brand, model, manufacturer_id) VALUES ('奥迪', 'A8', 2)")
    cursor.execute("INSERT INTO vehicles (brand, model, manufacturer_id) VALUES ('奔驰', 'C-Class', 3)")

    # 插入操作员信息
    cursor.execute("INSERT INTO operators (username, password, role) VALUES ('202235010623', '202235010623', 'admin')")
    cursor.execute("INSERT INTO operators (username, password, role) VALUES ('202235010611', '202235010611', 'admin')")
    cursor.execute("INSERT INTO operators (username, password, role) VALUES ('guest', 'guest', 'guest')")

    # 插入财务信息
    cursor.execute("INSERT INTO financials (vehicle_id, transaction_type, amount, customer_id, date) VALUES (2, '买入', 2, 2, '2024-12-04')")
    cursor.execute("INSERT INTO financials (vehicle_id, transaction_type, amount, customer_id, date) VALUES (3, '卖出', 1, 1, '2023-01-01')")

    # 插入客户信息
    cursor.execute("INSERT INTO customers (name) VALUES ('墨水厂')")
    cursor.execute("INSERT INTO customers (name) VALUES ('莫洛托夫')")

    # 提交事务
    conn.commit()
    # 关闭连接
    conn.close()

# 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
def connect_to_database():
    conn = sqlite3.connect('car_sales.db')
    cursor = conn.cursor()
    return conn, cursor

class car_sales_system(http.server.BaseHTTPRequestHandler):
    max_cache_time = 86400  # 最大缓存时间，单位为秒

    # 当客户端发送 GET 请求时
    def do_GET(self):
        try:
            # 格式化不符合规则的 URL
            if self.path.startswith('/./'):
                self.send_response(301)
                self.send_header('Location', self.path[2:])
                self.end_headers()
            # 当访问根目录或 index.html 时，返回首页
            elif self.path == '/' or self.path == '/index.html' or self.path.startswith('/?') or self.path.startswith('/index.html'):
                # 返回请求头
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', f'public, max-age={self.max_cache_time}')
                self.end_headers()
                # 返回页面内容
                self.wfile.write(self.generate_index_html())
            # 访问登陆页面
            elif self.path == '/login.html' or self.path.startswith('/login.html'):
                # 返回请求头
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', f'public, max-age={self.max_cache_time}')
                self.end_headers()
                # 返回页面内容
                self.wfile.write(self.generate_login_html())
            # 访问车辆管理页面
            elif self.path.startswith('/vehicles_management.html'):
                # 获取用户名和密码
                query_string = urlparse(self.path).query
                query_params = parse_qs(query_string)
                username = query_params.get('username', [''])[0]
                password = query_params.get('password', [''])[0]
                role = self.check_login(username, password)
                # 返回请求头
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                # 如果登录成功，则返回车辆管理页面否则报错并指引用户返回登录页面
                if role:
                    self.wfile.write(self.generate_vehicles_management_html(role))
                else:
                    self.wfile.write(self.generate_error_html(200, '用户名或密码有误。'))
            # 当访问 car_sales_system.css 时，返回样式表
            elif self.path == '/car_sales_system.css':
                # 返回请求头
                self.send_response(200)
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-type', 'text/css')
                self.send_header('Cache-Control', f'public, max-age={self.max_cache_time}')
                self.end_headers()
                # 返回样式表内容
                self.wfile.write(self.generate_css())
            # 当访问 favicon.ico 时，返回图标
            elif self.path == '/favicon.ico':
                # 返回请求头
                self.send_response(200)
                self.send_header('Content-type', 'image/svg+xml')
                self.send_header('Cache-Control', f'public, max-age={self.max_cache_time}')
                self.end_headers()
                # 返回图标内容
                self.wfile.write(self.generate_favicon())
            # 404
            else:
                self.send_msg_error(404, "未找到该资源。")
        except Exception as e:
            self.send_msg_error(500, f"服务器出错。<br>{e}")

    # 响应客户端的 POST 请求
    def do_POST(self):
        try:
            if self.path == '/add_message':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                brand = data.get('brand')
                model = data.get('model')
                manufacturer = data.get('manufacturer')
                operation = data.get('operation')
                quantity = int(data.get('quantity'))
                customername = data.get('customername')

                if (quantity < 1):
                    self.send_msg_error(400, "数量必须大于0！")
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'status': 'success', 'message': 'Data received'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                
                self.add_data(brand, model, manufacturer, operation, quantity, customername)
            else:
                self.send_msg_error(404, "未找到该资源。")
        except Exception as e:
            self.send_msg_error(500, f"服务器出错。<br>{e}")

    # 生成数据库连接页面
    def generate_index_html(self):
        return '''<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <link type="text/css" rel="stylesheet" href="car_sales_system.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据库连接</title>
</head>

<body>
    <div class="container">
        <fieldset>
            <legend>数据库连接</legend>
            <label for="servername">服务器名:</label>
            <input type="text" id="servername" name="servername" value="Local">
            <br>
            <label for="dbname">数据库名:</label>
            <input type="text" id="dbname" name="dbname" value="汽车销售系统">
            <br>
            <label for="username">用户名:</label>
            <input type="text" id="username" name="username" value="202235010623">
            <br>
            <label for="password">密码:</label>
            <input type="text" id="password" name="password" value="202235010623">
            <br>
            <button type="submit" onclick="validateForm()">连接</button>
            <button type="button" onclick="closeWindow()">取消</button>
        </fieldset>
        <script>
            function validateForm() {
                // 获取表单元素
                const servername = document.getElementById('servername').value;
                const dbname = document.getElementById('dbname').value;
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                // 验证服务器名 ,验证数据库名
                if ((servername !== 'Local') || (dbname !== '汽车销售系统')) {
                    setTimeout(() => {
                        alert('无法连接');
                    }, 1000);
                    return;
                }
                // 验证用户名
                if ((username === '202235010623' && password === '202235010623') || (username === '202235010611' && password === '202235010611')) {
                    window.location.href = "login.html";
                    return;
                }
                setTimeout(() => {
                    alert('无法连接');
                }, 1000);
            }
            function closeWindow() {
                window.close();
            }           
        </script>
    </div>
</body>

</html>'''.encode('utf-8')

    # 生成汽车销售登陆系统页面
    def generate_login_html(self):
        return '''<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <link type="text/css" rel="stylesheet" href="car_sales_system.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>汽车销售登陆系统</title>
</head>

<body>
    <div class="container">
        <fieldset>
            <legend>汽车销售登陆系统</legend>
            <label for="username">用户名:</label>
            <input type="text" id="username" name="username" value="202235010623">
            <br>
            <label for="password">密码:</label>
            <input type="text" id="password" name="password" value="202235010623">
            <br>
            <button type="submit" onclick="validateForm()">登陆</button>
            <button type="button" onclick="closeWindow()">取消</button>
        </fieldset>
        <script>
            function validateForm() {
                // 获取表单元素
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                //跳转到车辆管理页面
                window.location.href = "vehicles_management.html?username=" + username + "&password=" + password;
            }
            function closeWindow() {
                window.close();
            }           
        </script>
    </div>
</body>

</html>'''.encode('utf-8')
    
    # 生成车辆管理页面
    def generate_vehicles_management_html(self, role):
        control = ' style="display:none"'
        if role == 'admin':
            control = ''
        return f'''<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <link type="text/css" rel="stylesheet" href="car_sales_system.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>汽车管理系统</title>
</head>

<body>
    <div class="container" style="max-width: 800px;">
        <fieldset>
            <legend>汽车管理系统</legend>
            <a href="404.html">库存信息</a>
            <a href="login.html">退出登录</a>
        </fieldset>
        <fieldset{control}>
            <legend>操作</legend>
            <label for="brand">车辆品牌：</label>
            <input type="text" list="brand_list" id="brand" required>
            <datalist id="brand_list">
                <!-- 默认选项 -->
                {self.get_options('brand', 'vehicles')}
            </datalist>
            <br>
            <label for="model">车辆型号：</label>
            <input type="text" list="model_list" id="model" required>
            <datalist id="model_list">
                <!-- 默认选项 -->
                {self.get_options('model', 'vehicles')}
            </datalist>
            <br>
            <label for="manufacturer">车辆制造商：</label>
            <input type="text" list="manufacturer_list" id="manufacturer" required>
            <datalist id="manufacturer_list">
                <!-- 默认选项 -->
                {self.get_options('name', 'manufacturers')}
            </datalist>
            <br>
            <label for="operation">操作：</label>
            <input type="radio" name="operation" value="buy" required> 买入 <input type="radio" name="operation"
                value="sell" required> 卖出
            <br>
            <label for="quantity">数量：</label>
            <input type="number" id="quantity" required>
            <br>
            <label for="customername">客户信息：</label>
            <input type="text" list="customername_list" id="customername" required>
            <datalist id="customername_list">
                <!-- 默认选项 -->
                {self.get_options('name', 'customers')}
            </datalist>
            <br>
            <button id="submit">提交</button>
        </fieldset>
        <fieldset>
            <legend>交易信息</legend>
            <table>
                <thead>
                    <tr>
                        <th>车辆品牌</th>
                        <th>车辆型号</th>
                        <th>车辆制造商</th>
                        <th>操作</th>
                        <th>数量</th>
                        <th>客户信息</th>
                        <th>日期</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- 汽车数据将在这里动态生成 -->
                    {self.get_vehicle_transactions()}
                </tbody>
            </table>
        </fieldset>
    </div>

    <style>
        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th,
        td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background-color: #f2f2f2;
        }}
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            // 添加汽车
            document.querySelector('#submit').addEventListener('click', (e) => {{
                e.preventDefault();
                const brand = document.getElementById('brand').value;
                const model = document.getElementById('model').value;
                const radios = document.querySelectorAll('input[name="operation"]');
                var operation = null;
                radios.forEach(radio => {{
                    if (radio.checked) {{
                        operation = radio.value;
                    }}
                }});
                const manufacturer = document.getElementById('manufacturer').value;
                const quantity = parseInt(document.getElementById('quantity').value, 10);
                const customername = document.getElementById('customername').value;
                const illegal_chars = ['<', '>', '&', '"', "'", "\\\\"]

                // 检查非法字符
                function containsIllegalChars(str) {{
                    return illegal_chars.some(char => str.includes(char));
                }}

                // 检查数量是否为正
                function isNotPositiveNumber(num) {{
                    return num < 1;
                }}

                // 验证输入
                if (containsIllegalChars(brand) || containsIllegalChars(model) || containsIllegalChars(manufacturer) || containsIllegalChars(customername)) {{
                    alert('输入包含非法字符：<, >, &, ", \\', \\\\');
                    return;
                }}

                if (isNotPositiveNumber(quantity)) {{
                    alert('数量必须为正数');
                    return;
                }}

                // 构建请求体
                const data = {{
                    brand: brand,
                    model: model,
                    manufacturer: manufacturer,
                    operation: operation,
                    quantity: quantity,
                    customername: customername
                }};

                // 发送 POST 请求
                fetch('/add_message', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(data)
                }})
                    .then(response => {{
                        console.log('Success:', data);
                        window.location.reload();
                    }})
                    .catch((error) => {{
                        console.error('Error:', error);
                        alert(error);
                    }});
            }});
        }});
    </script>
</body>

</html>'''.encode('utf-8')
    
    # 生成图标
    def generate_favicon(self):
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><circle cx="25" cy="25" r="20" fill="green" /></svg>'''.encode('utf-8')

    # 生成样式表
    def generate_css(self):
        return f'''body{{font-family:Arial,sans-serif;background-color:#f4f4f4;margin:0;padding-top:20px;color:#333}}.hide{{display:none}}.container{{box-sizing:border-box;overflow:hidden;width:100%;max-width:600px;margin:0 auto;padding:20px;background-color:#fff;border:1px solid #ccc;box-shadow:2px 2px 5px rgba(0,0,0,0.1);border-radius:5px}}fieldset{{border:1px solid #ddd;padding:10px;margin-bottom:5px}}legend{{font-weight:bold;padding:0 10px}}label{{display:block;margin-bottom:5px}}input[type="text"],input[type="number"],iframe,.content{{box-sizing:border-box;max-width:100%;width:100%;padding:8px;margin-bottom:10px;border:1px solid #ddd;border-radius:3px}}a,a:visited,button{{align-items:center;text-decoration:none;padding:8px 15px;margin-right:5px;background-color:#007BFF;color:#fff;border:none;border-radius:3px;cursor:pointer}}a:hover,a:visited:hover,button:hover{{background-color:#0056b3}}button:active{{background-color:#0067b8}}@media (max-width:600px){{.container{{width:100%;height:100%;border:none;border-radius:0;box-shadow:none}}}}.loading-bar{{position:fixed;top:0;left:0;z-index:99999;opacity:0;transition:opacity .4s linear;.progress{{position:fixed;top:0;left:0;width:0;height:4px;background-color:#007bff;box-shadow:0 0 10px rgba(119,182,255,.7)}}&.loading{{opacity:1;transition:none;.progress{{transition:width .4s ease}}}}}}'''.encode('utf-8')

    # 生成报错误页面
    def generate_error_html(self, errorCode, errorMsg = '', buttons = "<a href='/login.html'>重新登录</a>"):
        if not errorMsg:
            errorMsg = f'错误代码：{errorCode}<br>Error code: {errorCode}'
        return f'''<!DOCTYPE html><html lang="zh-Hans"><head><meta charset="UTF-8"><title>错误：{errorCode}</title><link type="text/css" rel="stylesheet" href="/car_sales_system.css"><meta name="viewport" content="width=192, initial-scale=1.0"></head><body><div class="container"><fieldset><legend>错误：{errorCode}</legend><div class="content">{errorMsg}</div>{buttons}</fieldset></div><div class="loading-bar"><div class="progress"></div></div></body></html>'''.encode('utf-8')

    # 获取车辆交易信息
    def get_vehicle_transactions(self):
        conn, cursor = connect_to_database()
        cursor.execute('''
            SELECT t1.brand, t1.model, t3.name, t0.transaction_type, t0.amount, t2.name, t0.date 
            FROM financials t0, vehicles t1, customers t2, manufacturers t3
            WHERE t0.vehicle_id = t1.id AND t0.customer_id = t2.id AND t1.manufacturer_id = t3.id
        ''')
        raw = cursor.fetchall()
        conn.close()
        financials = ''
        for i in raw:
            financials += '<tr>'
            for j in i:
                financials += f'<td>{j}</td>'
            financials += '</tr>'
        return financials

    # 获取单个属性的所有数据
    def get_single_attribute_data(self, attribute, table_name):
        conn, cursor = connect_to_database()
        cursor.execute(f'SELECT DISTINCT {attribute} FROM {table_name}')
        data = cursor.fetchall()
        conn.close()
        return data

    # 获取单个属性的所有数据
    def get_options(self, attribute, table_name):
        raw = self.get_single_attribute_data(attribute, table_name)
        data = ''
        for i in raw:
            data += f'<option value="{i[0]}"></option>'
        return data

    # 是否存在某车辆
    def exist_vehicle(self, brand, model):
        pass
        conn, cursor = connect_to_database()

    # 整理数据并写入数据库
    def add_data(self, brand, model, manufacturer, operation, quantity, customername):
        if operation == 'sell':
            pass
        elif operation == 'buy':
            pass
        pass
    
    # 生成并返回错误页面头信息和页面内容
    def send_msg_error(self, errorCode, errorMsg = '', buttons = "<a href='/login.html'>重新登录</a>"):
        self.send_response(errorCode)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'public, max-age=5')
        self.end_headers()
        self.wfile.write(self.generate_error_html(errorCode, errorMsg, buttons))

    # 检查登录
    def check_login(self, username, password):
        conn, cursor = connect_to_database()
        # 从数据库中获取用户名和密码相对应的用户信息
        cursor.execute("SELECT role FROM operators WHERE username=? AND password=?", (username, password))
        role = cursor.fetchone()
        # 格式化 role
        role = role[0] if role else None
        conn.close()
        if role is not None:
            return role
        else:
            return role is not None

    # 检查字符串是否包含非法字符
    def check_string(self, string):
        # 非法字符集
        illegal_chars = ['<', '>', '&', '"', "'", "\\"]
        if any(char in string for char in illegal_chars):
            return False
        return True

# 初始化网页服务器
def initialize_server():
    parser = argparse.ArgumentParser(description='汽车销售系统')
    parser.add_argument('--port', type=int, default=2666, help='监听的端口')
    args = parser.parse_args()

    server_address = ('0.0.0.0', args.port)
    httpd = socketserver.TCPServer(server_address, car_sales_system)
    httpd.allow_reuse_address = True

    print(f'服务器地址：http://127.0.0.1:{args.port}')
    httpd.serve_forever()

if __name__ == '__main__':
    # 检查 car_sales.db 数据库是否存在
    if os.path.exists('car_sales.db'):
        os.remove('car_sales.db')
    if not os.path.exists('car_sales.db'):
        print("数据库不存在，正在创建...")
        initialize_database()
        initialize_data()
    initialize_server()
