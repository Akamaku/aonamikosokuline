from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3, itertools, csv, io

app = Flask(__name__)
app.secret_key = "liner-mars-secret"
DB_PATH = "mars.db"
STATIONS = ["青波中央", "青波西", "朝日ヶ丘", "高輪平", "船渡川", "南ヶ丘", "茶志内"]

def get_conn(): return sqlite3.connect(DB_PATH)

def station_index(name): return STATIONS.index(name)

def overlap(f1, t1, f2, t2): return (station_index(f1) < station_index(t2)) and (station_index(t1) > station_index(f2))

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_id INTEGER PRIMARY KEY, name TEXT, origin TEXT, destination TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cars (car_id INTEGER PRIMARY KEY, train_id INTEGER, car_number INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS seats (seat_id INTEGER PRIMARY KEY, car_id INTEGER, seat_number TEXT, is_window BOOLEAN)")
    c.execute("CREATE TABLE IF NOT EXISTS reservations (reservation_id INTEGER PRIMARY KEY, seat_id INTEGER, name TEXT, from_station TEXT, to_station TEXT, status TEXT)")
    conn.commit(); conn.close()

def seed_data():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM trains")
    if c.fetchone()[0] > 0:
        conn.close(); return
    for train_no in range(1, 41):
        if train_no % 2 == 1:
            origin, dest = "青波中央", "茶志内"
        else:
            origin, dest = "茶志内", "青波中央"
        c.execute("INSERT INTO trains (name, origin, destination) VALUES (?, ?, ?)", (f"ライナー{train_no}号", origin, dest))
        train_id = c.lastrowid
        for car_num in range(1, 4):
            c.execute("INSERT INTO cars (train_id, car_number) VALUES (?, ?)", (train_id, car_num))
            car_id = c.lastrowid
            for row, col in itertools.product(range(1, 19), ["A", "B", "C", "D"]):
                seat = f"{row}{col}"; is_window = col in ["A", "D"]
                c.execute("INSERT INTO seats (car_id, seat_number, is_window) VALUES (?, ?, ?)", (car_id, seat, is_window))
    conn.commit(); conn.close()

def get_seat_map(train_id, car_number):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT s.seat_number, CASE WHEN r.status='reserved' THEN 1 ELSE 0 END FROM seats s LEFT JOIN reservations r ON s.seat_id=r.seat_id AND r.status='reserved' JOIN cars c2 ON s.car_id=c2.car_id WHERE c2.train_id=? AND c2.car_number=? ORDER BY s.seat_number", (train_id, car_number))
    rows = c.fetchall(); conn.close()
    seat_map = {}
    for sn, res in rows:
        rownum = int(''.join(ch for ch in sn if ch.isdigit())); col = ''.join(ch for ch in sn if ch.isalpha())
        seat_map.setdefault(rownum, {})[col] = "×" if res else "◎"
    return seat_map

def try_reserve(train_id, car_number, seat, name, f, t):
    if station_index(f) >= station_index(t): return False, "出発駅は到着駅より前にしてください。"
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT s.seat_id FROM seats s JOIN cars c2 ON s.car_id=c2.car_id WHERE c2.train_id=? AND c2.car_number=? AND s.seat_number=?", (train_id, car_number, seat))
    row = c.fetchone()
    if not row: conn.close(); return False, "座席が見つかりません。"
    seat_id = row[0]
    c.execute("SELECT from_station,to_station FROM reservations WHERE seat_id=? AND status='reserved'", (seat_id,))
    for f2, t2 in c.fetchall():
        if overlap(f, t, f2, t2): conn.close(); return False, f"区間が重複（{f2}→{t2}）"
    c.execute("INSERT INTO reservations (seat_id, name, from_station, to_station, status) VALUES (?, ?, ?, ?, 'reserved')", (seat_id, name, f, t))
    conn.commit(); conn.close()
    return True, f"{car_number}号車 {seat}（{f}→{t}）を予約しました。"

def cancel_reservation(train_id, car_number, seat, name):
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT r.reservation_id FROM reservations r
        JOIN seats s ON r.seat_id=s.seat_id JOIN cars c2 ON s.car_id=c2.car_id
        WHERE c2.train_id=? AND c2.car_number=? AND s.seat_number=? AND r.name=? AND r.status='reserved'""", (train_id, car_number, seat, name))
    row = c.fetchone()
    if not row: conn.close(); return False, "予約が見つかりません。"
    c.execute("UPDATE reservations SET status='cancelled' WHERE reservation_id=?", (row[0],))
    conn.commit(); conn.close(); return True, f"{car_number}号車 {seat} の予約をキャンセルしました。"

@app.route("/")
def index(): return render_template("seat_map.html", mode="select_direction")

@app.route("/down")
def down_list():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT train_id,name FROM trains WHERE train_id % 2 = 1 ORDER BY train_id")
    trains = c.fetchall(); conn.close()
    return render_template("seat_map.html", mode="select_train", direction="下り（青波中央→茶志内）", trains=trains)

@app.route("/up")
def up_list():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT train_id,name FROM trains WHERE train_id % 2 = 0 ORDER BY train_id")
    trains = c.fetchall(); conn.close()
    return render_template("seat_map.html", mode="select_train", direction="上り（茶志内→青波中央）", trains=trains)
