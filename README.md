# 🚄 ライナー MARS 予約システム（フル機能版）

Flaskで構築した「青波線ライナー」座席予約システムです。  
ブラウザから上下線・列車・号車・座席を選択し、予約やキャンセルを行えます。

---

## 🧩 主な機能
- 上り／下りライナー（1〜40号）切り替え
- 各列車3両編成、座席は1A〜18D
- 予約／キャンセル機能（区間チェック付き）
- 管理画面で全予約を閲覧
- CSV出力機能

---

## ⚙️ 実行方法

1. 必要なライブラリをインストール
```bash
pip install flask
```

2. アプリを起動
```bash
python app.py
```

3. ブラウザでアクセス
```
http://127.0.0.1:5000/
```

---

## 💾 構成
```
liner_mars_system/
├── app.py
├── templates/
│   └── seat_map.html
├── static/
│   └── style.css
├── README.md
└── .gitignore
```

---

## 👑 ライセンス
MIT License
