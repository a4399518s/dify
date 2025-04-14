import logging
from datetime import UTC, datetime
import random
import string
from typing import Optional

import requests
from flask import current_app, redirect, request
from flask_restful import Resource  # type: ignore
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
from models.account import AccountStatus, Tenant
from services.account_service import AccountService, RegisterService, TenantService
from services.errors.account import AccountNotFoundError, AccountRegisterError
from services.errors.workspace import WorkSpaceNotAllowedCreateError, WorkSpaceNotFoundError
from services.feature_service import FeatureService

from .. import api


def get_oauth_providers():
    with current_app.app_context():
        if not dify_config.GITHUB_CLIENT_ID or not dify_config.GITHUB_CLIENT_SECRET:
            github_oauth = None
        else:
            github_oauth = GitHubOAuth(
                client_id=dify_config.GITHUB_CLIENT_ID,
                client_secret=dify_config.GITHUB_CLIENT_SECRET,
                redirect_uri=dify_config.CONSOLE_API_URL + "/console/api/oauth/authorize/github",
            )
        if not dify_config.GOOGLE_CLIENT_ID or not dify_config.GOOGLE_CLIENT_SECRET:
            google_oauth = None
        else:
            google_oauth = GoogleOAuth(
                client_id=dify_config.GOOGLE_CLIENT_ID,
                client_secret=dify_config.GOOGLE_CLIENT_SECRET,
                redirect_uri=dify_config.CONSOLE_API_URL + "/console/api/oauth/authorize/google",
            )

        wx_oauth = WxOAuth(
            client_id="wxd16fa5d21589fabd",
            client_secret="72aabbac34818a50ad7adb114ee9122b",
            # redirect_uri=dify_config.CONSOLE_API_URL + "/console/api/oauth/authorize/wx",
            redirect_uri="http://agent.hctalent.cn/console/api/oauth/authorize/wx",
        )

        OAUTH_PROVIDERS = {"github": github_oauth, "google": google_oauth, "wx": wx_oauth}
        return OAUTH_PROVIDERS


class OAuthLogin(Resource):
    def get(self, provider: str):
        tenant_names = request.args.get("tenant_names") or None
        OAUTH_PROVIDERS = get_oauth_providers()
        with current_app.app_context():
            oauth_provider = OAUTH_PROVIDERS.get(provider)
        if not oauth_provider:
            return {"error": "Invalid provider"}, 400

        auth_url = oauth_provider.get_authorization_url(tenant_names=tenant_names)
        return redirect(auth_url)


class OAuthCallback(Resource):
    def get(self, provider: str):
        OAUTH_PROVIDERS = get_oauth_providers()
        with current_app.app_context():
            oauth_provider = OAUTH_PROVIDERS.get(provider)
        if not oauth_provider:
            return {"error": "Invalid provider"}, 400
        code = request.args.get("code")
        state = request.args.get("state")
        logging.info(f"xxxxxxxxxxx OAuthCallback: {oauth_provider} {code} {state}")

        try:
            token = oauth_provider.get_access_token(code)
            user_info = oauth_provider.get_user_info(token)
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            logging.exception(f"An error occurred during the OAuth process with {provider}: {error_text}")
            return {"error": "OAuth process failed"}, 400

        try:
            account = _generate_account(provider, user_info,state)
        except AccountNotFoundError:
            return redirect(f"{dify_config.CONSOLE_WEB_URL}/signin?message=Account not found.")
        except (WorkSpaceNotFoundError, WorkSpaceNotAllowedCreateError):
            return redirect(
                f"{dify_config.CONSOLE_WEB_URL}/signin"
                "?message=Workspace not found, please contact system admin to invite you to join in a workspace."
            )
        except AccountRegisterError as e:
            return redirect(f"{dify_config.CONSOLE_WEB_URL}/signin?message={e.description}")

        # Check account status
        if account.status == AccountStatus.BANNED.value:
            return redirect(f"{dify_config.CONSOLE_WEB_URL}/signin?message=Account is banned.")

        if account.status == AccountStatus.PENDING.value:
            account.status = AccountStatus.ACTIVE.value
            account.initialized_at = datetime.now(UTC).replace(tzinfo=None)
            db.session.commit()

        try:
            TenantService.create_owner_tenant_if_not_exist(account)
        except Unauthorized:
            return redirect(f"{dify_config.CONSOLE_WEB_URL}/signin?message=Workspace not found.")
        except WorkSpaceNotAllowedCreateError:
            return redirect(
                f"{dify_config.CONSOLE_WEB_URL}/signin"
                "?message=Workspace not found, please contact system admin to invite you to join in a workspace."
            )

        token_pair = AccountService.login(
            account=account,
            ip_address=extract_remote_ip(request),
        )

        return redirect(
            f"{dify_config.CONSOLE_WEB_URL}?access_token={token_pair.access_token}&refresh_token={token_pair.refresh_token}"
        )


def _get_account_by_openid_or_email(provider: str, user_info: OAuthUserInfo) -> Optional[Account]:
    account: Optional[Account] = Account.get_by_openid(provider, user_info.id)

    if not account:
        with Session(db.engine) as session:
            account = session.execute(select(Account).filter_by(email=user_info.email)).scalar_one_or_none()

    return account


def _generate_account(provider: str, user_info: OAuthUserInfo,tenant_names: str = "") -> Account:
    # Get account by openid or email.
    account = _get_account_by_openid_or_email(provider, user_info)
    if not account:
        # if not FeatureService.get_system_features().is_allow_register:
        #     raise AccountNotFoundError()
        # account_name = user_info.name or "美数合"
        # account = RegisterService.register(
        #     email=user_info.email, name=account_name, password=None, open_id=user_info.id, provider=provider
        # )
        account = AccountService.create_account(user_info.email, user_info.name,''.join(random.sample(string.ascii_letters + string.digits, 8)))
        tenant = Tenant.query.filter(Tenant.name == "default").one_or_404();
        logging.info(f"tenant:{tenant}")
        TenantService.create_tenant_member(tenant,account,role="normal");
        TenantService.switch_tenant(account,tenant.id)
        if(tenant_names!=""):
            tenant_names = tenant_names.split(",")
            for tenant_name in tenant_names:
                tenant = Tenant.query.filter(Tenant.name == tenant_name).one_or_none();
                if tenant is None:
                    continue
                TenantService.create_tenant_member(tenant,account,role="normal")
                TenantService.switch_tenant(account,tenant.id)
        # Set interface language
        preferred_lang = request.accept_languages.best_match(languages)
        if preferred_lang and preferred_lang in languages:
            interface_language = preferred_lang
        else:
            interface_language = languages[0]
        account.interface_language = interface_language
        db.session.commit()

    # Link account
    AccountService.link_account_integrate(provider, user_info.id, account)

    return account


api.add_resource(OAuthLogin, "/oauth/login/<provider>")
api.add_resource(OAuthCallback, "/oauth/authorize/<provider>")
