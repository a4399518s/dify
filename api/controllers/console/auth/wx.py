import logging
from datetime import UTC, datetime
import random
import string
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
from models import Account

from models import AccountIntegrate, InvitationCode
from models.account import AccountStatus, Tenant
from services.account_service import AccountService, RegisterService, TenantService
from services.errors.account import AccountNotFoundError, AccountRegisterError
from services.errors.workspace import WorkSpaceNotAllowedCreateError, WorkSpaceNotFoundError
from services.feature_service import FeatureService

from .. import api
from wechatpy import WeChatClient,parse_message
from wechatpy.replies import TextReply


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

        client = WeChatClient('wxd16fa5d21589fabd', '72aabbac34818a50ad7adb114ee9122b')
        client.menu.create({
            "button":[
                {
                    "name":"AI",
                    "sub_button":[
                        {
                            "type":"view",
                            "name":"测试流程",
                            "url":"https://www.baidu.com"
                        }
                    ]
                },
                {
                    "name":"我的",
                    "sub_button":[
                        {
                            "type":"click",
                            "name":"我的积分1111",
                            "key":"MY_POINT"
                        }
                    ]
                }
            ]
        })
        return Response(echostr, mimetype='text/plain')
    
    def post(self):
        request_data = request.get_data().decode('utf-8')
        msg = parse_message(request_data)
        if msg.type == 'event' and msg.event == 'click' and msg.key == 'MY_POINT':
            openid = request.args.get('openid')
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
            
            reply = TextReply(content=f'您的积分:{account.point}', message=msg)
            # 转换成 XML
            xml = reply.render()
            return Response(xml, mimetype='text/plain')
        
        reply = TextReply(content=f'暂未处理，请联系管理员。', message=msg)
        # 转换成 XML
        xml = reply.render()
        return Response(xml, mimetype='text/plain')
    

api.add_resource(WxCallbackMessage, "/channel/wx/callback")
