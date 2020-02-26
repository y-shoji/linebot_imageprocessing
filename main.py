# coding: UTF-8

import os
import random
import cv2

from pathlib import Path
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage, ImageSendMessage, 
    VideoSendMessage, StickerSendMessage, AudioSendMessage, QuickReply, QuickReplyButton, MessageAction
)
from utils.image_processing import *

from utils.stylize_api import stylize_api
ghoul_api = stylize_api(mode="tokyo_ghoul")

app = Flask(__name__)

#環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

SRC_IMAGE_PATH = "static/images/{}.jpg"
MAIN_IMAGE_PATH = "static/images/{}_main.jpg"
PREVIEW_IMAGE_PATH = "static/images/{}_preview.jpg"
message_id = ""

def save_image(message_id, save_path):
    message_content = line_bot_api.get_message_content(message_id)
    with open(save_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

def make_button():
    message_template = TextSendMessage(
            text='select',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="A", text="text1")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="B", text="text2")
                    )
                ]
            )
    )
    return message_template

def cross_hatching(reply_token):
    global message_id
    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    main_image_path = MAIN_IMAGE_PATH.format(message_id)
    preview_image_path = PREVIEW_IMAGE_PATH.format(message_id)

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

    cv2.imwrite(str(main_image_path),img2)
    cv2.imwrite(str(preview_image_path),pre_img)

    image_message = ImageSendMessage(
        original_content_url=f"https://799cc32b.ngrok.io/{main_image_path}",   #直前の画像
        preview_image_url=f"https://799cc32b.ngrok.io/{preview_image_path}",
    )

    line_bot_api.reply_message(reply_token, image_message)

    src_image_path.unlink()

def ghoul_processing(reply_token):
    global message_id
    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    main_image_path = MAIN_IMAGE_PATH.format(message_id)
    preview_image_path = PREVIEW_IMAGE_PATH.format(message_id)

    img = cv2.imread(str(src_image_path))

    img2 = ghoul_api.stylzie(img)

    max_size = 224
    h,w =img2.shape[:2]

    if w <= h and h > max_size:
        proportion = h/max_size
        pre_img = cv2.resize(img2, (int(w*proportion)-1, int(h*proportion)-1))
    elif w > h and w > max_size:
        proportion = w/max_size
        pre_img = cv2.resize(img2, (int(w*proportion)-1, int(h*proportion)-1))

    cv2.imwrite(str(main_image_path),img2)
    cv2.imwrite(str(preview_image_path),pre_img)

    image_message = ImageSendMessage(
        original_content_url=f"https://799cc32b.ngrok.io/{main_image_path}",   #直前の画像
        preview_image_url=f"https://799cc32b.ngrok.io/{preview_image_path}",
    )

    line_bot_api.reply_message(reply_token, image_message)

    src_image_path.unlink()

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
    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text=message))
    if message == "text1":
        cross_hatching(event.reply_token)
    elif message == "text2":
        # cross_hatching(event.reply_token)
        ghoul_processing(event.reply_token)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{message}の処理が出来ませんでした。")
        )



@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    global message_id
    message_id = event.message.id
    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    
    
    save_image(message_id, src_image_path)
    line_bot_api.reply_message(event.reply_token, make_button())


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
