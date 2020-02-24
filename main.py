import os
import random

from pathlib import Path
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage, ImageSendMessage, 
    VideoSendMessage, StickerSendMessage, AudioSendMessage
)

app = Flask(__name__)

#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

SRC_IMAGE_PATH = "static/images/{}.jpg"

def save_image(message_id: str, save_path: str) -> None:
    message_content = line_bot_api.get_message_content(message_id)
    with open(save_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()

    save_image(message_id, src_image_path)

    image_message = ImageSendMessage(
        original_content_url=f"https://rinebot114514.herokuapp.com/{src_image_path}",
        preview_image_url=f"https://rinebot114514.herokuapp.com/{src_image_path}",
    )
    line_bot_api.reply_message(event.reply_token, image_message)
    
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
