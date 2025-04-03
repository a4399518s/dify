from typing import cast
import logging

import flask_login  # type: ignore
from flask import request
from flask_restful import Resource, reqparse  # type: ignore

import services
from configs import dify_config
from constants.languages import languages
from controllers.console import api
from controllers.console.auth.error import (
    EmailCodeError,
    EmailOrPasswordMismatchError,
    EmailPasswordLoginLimitError,
    InvalidEmailError,
    InvalidTokenError,
)
from controllers.console.error import (
    AccountBannedError,
    AccountInFreezeError,
    AccountNotFound,
    EmailSendIpLimitError,
    NotAllowedCreateWorkspace,
)
from controllers.console.wraps import setup_required
from events.tenant_event import tenant_was_created
from libs.helper import email, extract_remote_ip
from libs.password import valid_password
from models.account import Account, Tenant
from services.account_service import AccountService, RegisterService, TenantService
from services.billing_service import BillingService
from services.errors.account import AccountRegisterError
from services.errors.workspace import WorkSpaceNotAllowedCreateError
from services.feature_service import FeatureService


class RegisterApi(Resource):
    """Resource for user login."""

    @setup_required
    def post(self):
        """Authenticate user and login."""
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=email, required=True, location="json")
        parser.add_argument("name", type=str, required=True, location="json")
        parser.add_argument("password", type=valid_password, required=True, location="json")
        parser.add_argument("language", type=str, required=False, default="en-US", location="json")
        parser.add_argument("tenant_names", type=str, required=False, default="", location="json")
        args = parser.parse_args()

        if dify_config.BILLING_ENABLED and BillingService.is_email_in_freeze(args["email"]):
            raise AccountInFreezeError()

        is_login_error_rate_limit = AccountService.is_login_error_rate_limit(args["email"])
        if is_login_error_rate_limit:
            raise EmailPasswordLoginLimitError()

        if args["language"] is not None and args["language"] == "zh-Hans":
            language = "zh-Hans"
        else:
            language = "en-US"

        try:
            account = AccountService.create_account(args["email"], args["name"],language,args["password"])
        except services.errors.account.AccountLoginError:
            raise AccountBannedError()
        except services.errors.account.AccountPasswordError:
            AccountService.add_login_error_rate_limit(args["email"])
            raise EmailOrPasswordMismatchError()
        except services.errors.account.AccountNotFoundError:
            if FeatureService.get_system_features().is_allow_register:
                token = AccountService.send_reset_password_email(email=args["email"], language=language)
                return {"result": "fail", "data": token, "code": "account_not_found"}
            else:
                raise AccountNotFound()
        tenant = Tenant.query.filter(Tenant.name == "default").one_or_404();
        logging.info(f"tenant:{tenant}")
        TenantService.create_tenant_member(tenant,account,role="normal");
        TenantService.switch_tenant(account,tenant.id)
        if(args["tenant_names"]!=""):
            tenant_names = args["tenant_names"].split(",")
            for tenant_name in tenant_names:
                tenant = Tenant.query.filter(Tenant.name == tenant_name).one_or_none();
                if tenant is None:
                    continue
                TenantService.create_tenant_member(tenant,account,role="normal")
                TenantService.switch_tenant(account,tenant.id)

        # SELF_HOSTED only have one workspace
        tenants = TenantService.get_join_tenants(account)
        if len(tenants) == 0:
            return {
                "result": "fail",
                "data": "workspace not found, please contact system admin to invite you to join in a workspace",
            }
        token_pair = AccountService.login(account=account, ip_address=extract_remote_ip(request))
        AccountService.reset_login_error_rate_limit(args["email"])
        return {"result": "success", "data": token_pair.model_dump()}


api.add_resource(RegisterApi, "/register")
