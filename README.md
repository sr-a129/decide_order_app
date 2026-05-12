
# Tennis Match Manager v3

## 追加機能
- CSVアップロード
- CSVからプレイヤー読み込み
- 紅白自動生成
- 試合自動生成
- コート自動割当
- ラウンド自動生成

## CSV形式

名前,性別,学年,実力,組みたい,組みたくない

## 起動方法

### Backend

pip install fastapi uvicorn python-multipart

uvicorn main:app --reload

### Frontend

npm install

npm run dev
