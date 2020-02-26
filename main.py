import os
import random
import cv2

from pathlib import Path
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage, ImageSendMessage, 
    VideoSendMessage, StickerSendMessage, AudioSendMessage
)
from utils.image_processing import *
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    TemplateSendMessage,ButtonsTemplate,URIAction 
)

app = Flask(__name__)

#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

SRC_IMAGE_PATH = "static/images/{}.jpg"
MAIN_IMAGE_PATH = "static/images/{}_main.jpg"
PREVIEW_IMAGE_PATH = "static/images/{}_preview.jpg"

def save_image(message_id: str, save_path: str) -> None:
    message_content = line_bot_api.get_message_content(message_id)
    with open(save_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

def make_button_template():
    message_template = TemplateSendMessage(
        template=ButtonsTemplate(
            title="選択してください",
            text="どの変換にする？",
            actions=[
                PostbackAction(label='A', data='AAA'),
                PostbackAction(label='B', data='BBB'),
            ]
        )
    )
    return message_template

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
    main_image_path = MAIN_IMAGE_PATH.format(message_id)
    preview_image_path = PREVIEW_IMAGE_PATH.format(message_id)
    
    save_image(message_id, src_image_path)

    img = cv2.imread(str(src_image_path),0)

    hatching45_img, hatching135_img = hatching(img, LIY=30)
    img2 = BD(hatching45_img, hatching135_img)
    
    max_size = 224
    h,w =img2.shape[:2]

    if w <= h and h > max_size:
        proportion = h/max_size
        pre_img = cv2.resize(img2, (int(w*proportion)-1, int(h*proportion)-1))
    elif w > h and w > max_size:
        proportion = w/max_size
        pre_img = cv2.resize(img2, (int(w*proportion)-1, int(h*proportion)-1))
    
    app.logger.info(img2.shape,pre_img.shape)

    cv2.imwrite(str(main_image_path),img2)
    cv2.imwrite(str(preview_image_path),pre_img)

    app.logger.info(os.path.isfile(f"https://date-the-image.herokuapp.com/{main_image_path}"))
    app.logger.info(os.path.isfile(f"https://date-the-image.herokuapp.com/{preview_image_path}"))

    image_message = ImageSendMessage(
        original_content_url=f"https://rinebot114514.herokuapp.com/{main_image_path}",
        preview_image_url=f"https://rinebot114514.herokuapp.com/{preview_image_path}",
    )

    line_bot_api.reply_message(event.reply_token, [make_button_template(), image_message])

    src_image_path.unlink()
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
