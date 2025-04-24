import logging
from datetime import UTC, datetime
import random
import re
import string
import threading
from typing import Optional

import requests
from flask import current_app, redirect, request,Response
from flask_restful import Resource, reqparse

from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.exceptions import Unauthorized

from configs import dify_config
from constants.languages import languages
from events.tenant_event import tenant_was_created
from extensions.ext_database import db
from libs.helper import extract_remote_ip
from libs.oauth import GitHubOAuth, GoogleOAuth, OAuthUserInfo, WxOAuth
from models import Account,Conversation, Site

from models import AccountIntegrate, InvitationCode
from models.account import AccountStatus, Tenant
from services.account_service import AccountService, RegisterService, TenantService
from services.errors.account import AccountNotFoundError, AccountRegisterError
from services.errors.workspace import WorkSpaceNotAllowedCreateError, WorkSpaceNotFoundError
from services.feature_service import FeatureService

from .. import api
from wechatpy import WeChatClient,parse_message
from wechatpy.replies import TextReply,EmptyReply
import hashlib
import requests

appId='wxe35e6bd987043ea1'
appSecret='e41e275f19a71b7b6c772807317c002c'
client = WeChatClient(appId, appSecret)

def ask_question(prompt: str, model: str = "qwq:latest", host: str = "http://ollama.fzh.cloud"):
    url = f"{host}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],"stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求出错: {e}")
        return None
def work(msg,openid, content):
    logging.info(f"xxxxxxxxxxx WxCallbackMessage content: {content}")
    content = ask_question(content)["message"]["content"]
    logging.info(f"xxxxxxxxxxx WxCallbackMessage content: {content}")
    match = re.search(r"<think>(.*?)</think>(.*)", content, re.DOTALL)
    if match:
        think_content = match.group(1).strip()
        after_think = match.group(2).strip()
        logging.info(f"xxxxxxxxxxx WxCallbackMessage think_content: {think_content}")
        logging.info(f"xxxxxxxxxxx WxCallbackMessage after_think: {after_think}")
        client.message.send_text(openid, after_think)
    
class WxCallbackMessage(Resource):
    def get(self):
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        # parser = reqparse.RequestParser()
        # parser.add_argument("signature", type=str, required=True)
        # parser.add_argument("timestamp", type=str, required=True)
        # parser.add_argument("nonce", type=str, required=True)
        # parser.add_argument("echostr", type=str, required=True)
        # args = parser.parse_args()
        logging.info(f"xxxxxxxxxxx WxCallbackMessage: {echostr}")

        res = client.menu.create({
            "button":[
                {
                    "name":"AI",
                    "sub_button":[
                        {
                            "type":"view",
                            "name":"小红书起号",
                            "url":"https://agent.meishuhe.cn/chat/rprpslItIapHedAt"
                        },
                        {
                            "type":"view",
                            "name":"数字人成片脚本",
                            "url":"https://agent.meishuhe.cn/chat/QVK5g3vYXvspTrNw"
                        }
                    ]
                },
                {
                    "name":"我的",
                    "sub_button":[
                        {
                            "type":"view",
                            "name":"我的信息",
                            "url":"http://agent.meishuhe.cn/my"
                        }
                    ]
                }
            ]
        })
        logging.info(f"xxxxxxxxxxx WxCallbackMessage:xxxxxx {res}")
        return Response(echostr, mimetype='text/plain')
    
    def post(self):
        request_data = request.get_data().decode('utf-8')
        msg = parse_message(request_data)
        logging.info(f"xxxxxxxxxxx WxCallbackMessage: {msg.type}")
        openid = request.args.get('openid')
        if msg.type == 'event' :
            logging.info(f"xxxxxxxxxxx WxCallbackMessage: {msg.event}")
            if msg.event == 'subscribe':
                reply = TextReply(content=f'欢迎关注美数合', message=msg)
                # 转换成 XML
                xml = reply.render()
                return Response(xml, mimetype='text/plain')
            if msg.event == 'unsubscribe':
                return Response("", mimetype='text/plain')
                
        if msg.type == 'event' and msg.event == 'click' and msg.key == 'MY_INFO':
            account_integrates = db.session.query(AccountIntegrate).filter(AccountIntegrate.open_id == openid).one_or_none()
            if account_integrates is None:
                reply = TextReply(content='您尚未登陆。', message=msg)
                # 转换成 XML
                xml = reply.render()
                return Response(xml, mimetype='text/plain')
            account = db.session.query(Account).filter(Account.id == account_integrates.account_id).one_or_none()
            if account_integrates is None:
                reply = TextReply(content='您尚未登陆!!!', message=msg)
                # 转换成 XML
                xml = reply.render()
                return Response(xml, mimetype='text/plain')
            
            reply = TextReply(content=f'您的积分:{account.point}\n您的ID:{account.id}\n您的open_id:{openid}\n', message=msg)
            # 转换成 XML
            xml = reply.render()
            return Response(xml, mimetype='text/plain')
        if msg.type == 'text':
            content = msg.content
            t = threading.Thread(target=work, args=(msg,openid, content))
            t.start()
            return Response("", mimetype='text/plain')
            
        return Response("", mimetype='text/plain')
    
class WxConfigMessage(Resource):
    def get(self):
        url = request.args.get('url')
        timestamp = int(datetime.now(UTC).timestamp())
        nonce_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        jsapi_ticket = client.jsapi.get_jsapi_ticket()
        signature = f'jsapi_ticket={jsapi_ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}'
        signature = hashlib.sha1(signature.encode('utf-8')).hexdigest()

        return {
            "result": "success", "data": {
            "debug": False, 
            "appId": appId,
            "timestamp": timestamp,
            "nonceStr": nonce_str,
            "signature": signature,
            "jsApiList": [],
            "openTagList": ["wx-open-subscribe"]
        }}

class WxPushMessage(Resource):
    def get(self):
        dify_conversation_id = request.args.get('dify_conversation_id')
        url = request.args.get('url')
        conversation = db.session.query(Conversation).filter(Conversation.id == dify_conversation_id).one_or_none()
        account_integrates = db.session.query(AccountIntegrate).filter(AccountIntegrate.account_id == conversation.from_account_id).one_or_none()
        # site = db.session.query(Site).filter(Site.app_id == conversation.app_id, Site.status == "normal").first()
        
        if account_integrates is None:
            return {"result": "error", "message": "用户不存在"}, 400
        res = client.message.send_subscribe_message(
            account_integrates.open_id,
            # 'daRbCWvn3k2LDdWP6Atfm7CGYGuB-Zo87s6Ng2HrszM', ## 美数合
            'ryq4gI3ZZftKKXaxPShUYPS-ti1pb2g92k_BSYCZ9DQ', ## 循圣堂
            {
                'thing1': {'value': 'AI视频'},
                'time2': {'value': datetime.now().strftime('%Y/%m/%d %H:%M')},
                'thing3': {'value': "您的视频生成成功，请进入菜单查看"},
                # 按照你的模板字段来填写
            },None,url
        )
        logging.info(f"xxxxxxxxxxx WxCallbackMessage: {res}")

api.add_resource(WxPushMessage, "/channel/wx/push-message")
api.add_resource(WxCallbackMessage, "/channel/wx/callback")
api.add_resource(WxConfigMessage, "/channel/wx/config")
