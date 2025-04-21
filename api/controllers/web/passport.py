import logging
import uuid

from flask import request
from flask_restful import Resource  # type: ignore
from werkzeug.exceptions import NotFound, Unauthorized

from controllers.web import api
from controllers.web.error import WebSSOAuthRequiredError
from extensions.ext_database import db
from libs.passport import PassportService
from models.model import App, EndUser, Site
from services.enterprise.enterprise_service import EnterpriseService
from services.feature_service import FeatureService


class PassportResource(Resource):
    """Base resource for passport."""

    def get(self):
        logging.info(f"xxxxxxxxxxx passport")
        system_features = FeatureService.get_system_features()
        app_code = request.headers.get("X-App-Code")
        app_token = request.headers.get("X-App-Token")
        if app_code is None:
            logging.info(f"xxxxxxxxxxx passport content: X-App-Code header is missing")
            raise Unauthorized("X-App-Code header is missing.")
        if app_token is None:
            logging.info(f"xxxxxxxxxxx passport content: X-App-Token header is missing")
            raise Unauthorized("X-App-Token header is missing.")

        logging.info(f"xxxxxxxxxxx passport 222")
        if system_features.sso_enforced_for_web:
            app_web_sso_enabled = EnterpriseService.get_app_web_sso_enabled(app_code).get("enabled", False)
            if app_web_sso_enabled:
                logging.info(f"xxxxxxxxxxx passport content: WebSSOAuthRequiredError")
                raise WebSSOAuthRequiredError()


        logging.info(f"xxxxxxxxxxx passport 333")
        # get site from db and check if it is normal
        site = db.session.query(Site).filter(Site.code == app_code, Site.status == "normal").first()
        if not site:
            logging.info(f"xxxxxxxxxxx passport content: site error")
            raise NotFound()
        logging.info(f"xxxxxxxxxxx passport 444")
        # get app from db and check if it is normal and enable_site
        app_model = db.session.query(App).filter(App.id == site.app_id).first()
        if not app_model or app_model.status != "normal" or not app_model.enable_site:
            logging.info(f"xxxxxxxxxxx passport content: app_model error")
            raise NotFound()
        
        # logging.info(f"xxxxxxxxxxx passport 555")
        decoded = PassportService().verify(app_token)
        # logging.info(f"xxxxxxxxxxx passport 555  111")
        if not decoded:
            logging.info(f"xxxxxxxxxxx passport token verify error")
            raise Unauthorized("X-App-Token header is missing.")
        logging.info(f"xxxxxxxxxxx passport 666")
        user_id = decoded.get("user_id")
        payload = {
            "iss": site.app_id,
            "sub": "Web API Passport",
            "app_id": site.app_id,
            "app_code": app_code,
            # "end_user_id": end_user.id,
            "user_id": user_id,
        }

        tk = PassportService().issue(payload)

        return {
            "access_token": tk,
        }


api.add_resource(PassportResource, "/passport")


def generate_session_id():
    """
    Generate a unique session ID.
    """
    while True:
        session_id = str(uuid.uuid4())
        existing_count = db.session.query(EndUser).filter(EndUser.session_id == session_id).count()
        if existing_count == 0:
            return session_id
