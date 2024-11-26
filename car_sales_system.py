import argparse
import os
import http.server
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
            amount REAL,
            date TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
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

    # 插入车辆信息
    cursor.execute("INSERT INTO vehicles (brand, model, manufacturer_id) VALUES ('BMW', 'X5', 1)")
    cursor.execute("INSERT INTO vehicles (brand, model, manufacturer_id) VALUES ('Audi', 'A8', 2)")
    cursor.execute("INSERT INTO vehicles (brand, model, manufacturer_id) VALUES ('Mercedes-Benz', 'C-Class', 3)")
    
    # 插入厂商信息
    cursor.execute("INSERT INTO manufacturers (name) VALUES ('BMW')")
    cursor.execute("INSERT INTO manufacturers (name) VALUES ('Audi')")
    cursor.execute("INSERT INTO manufacturers (name) VALUES ('Mercedes-Benz')")

    # 插入操作员信息
    cursor.execute("INSERT INTO operators (username, password, role) VALUES ('202235010623', '202235010623', 'admin')")
    cursor.execute("INSERT INTO operators (username, password, role) VALUES ('202235010611', '202235010611', 'admin')")
    cursor.execute("INSERT INTO operators (username, password, role) VALUES ('guest', 'guest', 'guest')")

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
                role = query_params.get('role', [''])[0]
                # 返回请求头
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', f'public, max-age={self.max_cache_time}')
                self.end_headers()
                # 如果登录成功，则返回车辆管理页面否则报错并指引用户返回登录页面
                if (self.check_login(username, password)):
                    self.wfile.write(self.generate_vehicles_management_html(username, password, role))
                else:
                    self.wfile.write(self.generate_error_html(200, '用户名或密码有误。'))
            # 当访问 main.css 时，返回样式表
            elif self.path == '/main.css':
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
                post_data = parse_qs(post_data)
                model = post_data.get('model', [''])[0]
                brand = post_data.get('brand', [''])[0]
                transaction_type = post_data.get('transaction_type', [''])[0]
                amount = post_data.get('amount', [''])[0]
                date = # TODO
                customer_name = post_data.get('customer_name', [''])[0]
            else:
                self.send_msg_error(404, "未找到该资源。")
        except Exception as e:
            self.send_msg_error(500, f"服务器出错。<br>{e}")

    # 生成图标
    def generate_favicon(self):
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"><circle cx="25" cy="25" r="20" fill="blue" /></svg>'''.encode('utf-8')

    # 生成样式表
    def generate_css(self):
        return f'''body{{font-family:Arial,sans-serif;background-color:#f4f4f4;margin:0;padding-top:20px;color:#333}}.hide{{display:none}}.container{{box-sizing:border-box;overflow:hidden;width:100%;max-width:600px;margin:0 auto;padding:20px;background-color:#fff;border:1px solid #ccc;box-shadow:2px 2px 5px rgba(0,0,0,0.1);border-radius:5px}}fieldset{{border:1px solid #ddd;padding:10px;margin-bottom:5px}}legend{{font-weight:bold;padding:0 10px}}label{{display:block;margin-bottom:5px}}input[type="text"],iframe,.content{{box-sizing:border-box;max-width:100%;width:100%;padding:8px;margin-bottom:10px;border:1px solid #ddd;border-radius:3px}}a,a:visited,button{{align-items:center;text-decoration:none;padding:8px 15px;margin-right:5px;background-color:#007BFF;color:#fff;border:none;border-radius:3px;cursor:pointer}}a:hover,a:visited:hover,button:hover{{background-color:#0056b3}}button:active{{background-color:#0067b8}}@media (max-width:600px){{.container{{width:100%;height:100%;border:none;border-radius:0;box-shadow:none}}}}.loading-bar{{position:fixed;top:0;left:0;z-index:99999;opacity:0;transition:opacity .4s linear;.progress{{position:fixed;top:0;left:0;width:0;height:4px;background-color:#007bff;box-shadow:0 0 10px rgba(119,182,255,.7)}}&.loading{{opacity:1;transition:none;.progress{{transition:width .4s ease}}}}}}'''.encode('utf-8')

    # 生成报错误页面
    def generate_error_html(self, errorCode, errorMsg = '', buttons = "<a href='/login.html'>重新登录</a>"):
        if not errorMsg:
            errorMsg = f'错误代码：{errorCode}<br>Error code: {errorCode}'
        return f'''<!DOCTYPE html><html lang="zh-Hans"><head><meta charset="UTF-8"><title>错误：{errorCode}</title><link type="text/css" rel="stylesheet" href="/main.css"><meta name="viewport" content="width=192, initial-scale=1.0"></head><body><div class="container"><fieldset><legend>错误：{errorCode}</legend><div class="content">{errorMsg}</div>{buttons}</fieldset></div><div class="loading-bar"><div class="progress"></div></div></body></html>'''.encode('utf-8')

    # 生成并返回错误页面头信息和页面内容
    def send_msg_error(self, errorCode, errorMsg = '', buttons = "<a href='/login.html'>重新登录</a>"):
        self.send_response(errorCode)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'public, max-age=15')
        self.end_headers()
        self.wfile.write(self.generate_error_html(errorCode, errorMsg, buttons))

    # 检查登录
    def check_login(self, username, password):
        conn, cursor = connect_to_database()
        cursor.execute("SELECT * FROM operators WHERE username=? AND password=?", (username, password))
        conn.close()

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
    if not os.path.exists('car_sales.db'):
        print("数据库不存在，正在创建...")
        initialize_database()
        initialize_data()
    initialize_server()
