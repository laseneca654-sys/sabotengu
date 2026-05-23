import asyncio
import websockets
import os
import json

# ルームごとの情報を管理する辞書
# 構造: { "ルームID": { "password": "パスワード", "clients": set(websocket1, websocket2...) } }
ROOMS = {}

async def handle_client(websocket):
    client_room = None

    try:
        async for message in websocket:
            try:
                # 送られてきたメッセージをJSONとして読み込む
                data = json.loads(message)
                room_id = data.get("room_id")
                password = data.get("password")

                # ルームIDかパスワードが含まれていない不正な通信は無視
                if not room_id or not password:
                    continue

                # そのクライアントがまだルームに割り当てられていない場合（接続後の初回メッセージ）
                if client_room is None:
                    if room_id not in ROOMS:
                        # まだそのルームが存在しなければ、パスワードを設定して新規作成
                        ROOMS[room_id] = {"password": password, "clients": set()}
                    elif ROOMS[room_id]["password"] != password:
                        # 既存のルームに違うパスワードで入ろうとした場合は強制切断
                        await websocket.close(1008, "Invalid password")
                        return
                    
                    # ルームに参加させる
                    ROOMS[room_id]["clients"].add(websocket)
                    client_room = room_id

                # 自分と同じルームにいる他のメンバーにだけメッセージを転送する
                if client_room == room_id:
                    # イテレーション中のエラーを防ぐため、リスト化して回す
                    for client in list(ROOMS[client_room]["clients"]):
                        if client != websocket:
                            try:
                                await client.send(message)
                            except:
                                # 万が一送信に失敗した（すでに切断されていた）場合はリストから除外
                                ROOMS[client_room]["clients"].discard(client)

            except json.JSONDecodeError:
                # JSON形式ではないデタラメな攻撃メッセージ等はすべて無視
                pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # クライアントがアプリを閉じた（切断された）時の後処理
        if client_room and client_room in ROOMS:
            ROOMS[client_room]["clients"].discard(websocket)
            # ルームから誰もいなくなったら、サーバーのメモリ節約のためにルーム自体を削除する
            if not ROOMS[client_room]["clients"]:
                del ROOMS[client_room]

async def main():
    port = int(os.environ.get("PORT", 8888))
    print(f"セキュアな家族専用サーバーをポート {port} で起動しました！")
    
    async with websockets.serve(handle_client, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
