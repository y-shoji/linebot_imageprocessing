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

from utils.aws_api import *

from utils.stylize_api import stylize_api
ghoul_api = stylize_api(mode="tokyo_ghoul")
mosaic_api = stylize_api(mode="mosaic")

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
            text='変換方法を選んでください',
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=MessageAction(label="クロスハッチング", text="クロスハッチング")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="東京喰種風", text="東京喰種風")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="ステンドグラス風", text="ステンドグラス風")
                    ),
                    QuickReplyButton(
                        action=MessageAction(label="ポスター風", text="ポスター風")
                    ),
                ]
            )
    )
    return message_template

def resize(img, max_size):

    h, w = img.shape[:2]

    if w <= h and h > max_size:
        proportion = max_size/h
    elif w > h and w > max_size:
        proportion = max_size/w
    else:
        proportion = 1
        
    img = cv2.resize(img, (int(w*proportion), int(h*proportion)))
    
    return img

def image_converter(reply_token, mode=0):
    """
    0: cross_hatching
    1: tokyo_ghoul
    """
    global message_id
    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    main_image_path = MAIN_IMAGE_PATH.format(message_id)
    preview_image_path = PREVIEW_IMAGE_PATH.format(message_id)

    img = cv2.imread(str(src_image_path))

    print(img.shape)
    img = resize(img=img, max_size=1024)
    print(img.shape)

    if mode == 0:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hatching45_img, hatching135_img = hatching(img, LIY=30)
        img2 = BD(hatching45_img, hatching135_img)
    elif mode == 1:
        img2 = ghoul_api.stylzie(img)
    elif mode == 2:
        img2 = mosaic_api.stylzie(img)
    elif mode == 3:
        img2 = Posterization_transfer(img)

    pre_img = resize(img=img2, max_size=224)

    cv2.imwrite(str(main_image_path),img2)
    cv2.imwrite(str(preview_image_path),pre_img)

    # image_message = ImageSendMessage(
    #     original_content_url=f"https://ad8e83cc.ngrok.io/{main_image_path}",
    #     preview_image_url=f"https://ad8e83cc.ngrok.io/{preview_image_path}",
    # )

    aws_save_image(str(main_image_path))
    aws_save_image(str(preview_image_path))

    image_message = ImageSendMessage(
        original_content_url=aws_get_url(str(main_image_path)),
        preview_image_url=aws_get_url(str(preview_image_path)),
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
    if message == "クロスハッチング":
        image_converter(event.reply_token, 0)
    elif message == "東京喰種風":
        image_converter(event.reply_token, 1)
    elif message == "ステンドグラス風":
        image_converter(event.reply_token, 2)
    elif message == "ポスター風":
        image_converter(event.reply_token, 3)
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
