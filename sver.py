import asyncio
import websockets
import os

CLIENTS = set()

async def handle_client(websocket):
    # 誰かが接続してきたらリストに追加
    CLIENTS.add(websocket)
    try:
        async for message in websocket:
            # メッセージを受け取ったら、自分以外の全員に転送する
            for client in CLIENTS:
                if client != websocket:
                    try:
                        await client.send(message)
                    except:
                        pass
    except:
        pass
    finally:
        # 切断されたらリストから消す
        CLIENTS.remove(websocket)

async def main():
    # クラウド（Render）が自動で割り当てるポート番号を取得
    port = int(os.environ.get("PORT", 8888))
    print(f"クラウドお見合い所をポート {port} で起動しました！")
    
    # 0.0.0.0 は「外からのアクセスを許可する」という意味（クラウド上なので安全です）
    async with websockets.serve(handle_client, "0.0.0.0", port):
        await asyncio.Future()  # サーバーを永遠に動かし続ける

if __name__ == "__main__":
    asyncio.run(main())