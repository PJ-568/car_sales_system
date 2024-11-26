import os
import http.server
import sqlite3

# 初始化数据库结构
def initialize_database():
    # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
    conn = sqlite3.connect('car_sales.db')
    cursor = conn.cursor()

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
    conn = sqlite3.connect('car_sales.db')
    cursor = conn.cursor()

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

def connect_to_database():
    # 连接到 SQLite 数据库
    conn = sqlite3.connect('car_sales.db')
    cursor = conn.cursor()
    return conn, cursor

def main(conn, cursor):
    pass

if __name__ == '__main__':
    # 检查 car_sales.db 数据库是否存在
    if not os.path.exists('car_sales.db'):
        print("数据库不存在，正在创建...")
        initialize_database()
        initialize_data()
    initialize_server()
    # conn, cursor = connect_to_database()
    # print("数据库连接成功")
    # main(conn, cursor)
    # # 关闭连接
    # conn.close()