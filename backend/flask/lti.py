# lti.py
import os
from flask import Blueprint, request, jsonify, session, redirect, url_for
from pylti1p3.tool_config import ToolConfDict
from pylti1p3.registration import Registration
from pylti1p3.message_launch import MessageLaunch
from pylti1p3.exception import LtiException
from pylti1p3.cookie import CookieService
from pylti1p3.launch_data_storage.cache import CacheDataStorage
from dotenv import load_dotenv

lti_bp = Blueprint("lti_bp", __name__)

load_dotenv()

# Load Private/Public Key from Environment Variables
private_key_pem = os.environ.get("LTI_PRIVATE_KEY", "")
public_key_pem = os.environ.get("LTI_PUBLIC_KEY", "")
if not private_key_pem:
    raise RuntimeError("Missing LTI_PRIVATE_KEY in environment!")
if not public_key_pem:
    raise RuntimeError("Missing LTI_PUBLIC_KEY in environment!")

# Build a pylti1p3 config dictionary for ufldev Canvas domain
issuer = "https://ufldev.instructure.com"
client_id = os.environ.get("LTI_CLIENT_ID")
deployment_id = os.environ.get("LTI_DEPLOYMENT_ID")

config_dict = {
        issuer: [ 
            {
                "default": True,
                "client_id": client_id,
                "auth_login_url": f"{issuer}/api/lti/authorize_redirect",
                "auth_token_url": f"{issuer}/login/oauth2/token",
                "auth_server": issuer,
                "key_set_url": "https://ufldev.instructure.com/api/lti/security/jwks",
                "deployment_ids": [
                    deployment_id
                ]
            }
        ]
}

# Create the pylti1p3 config
tool_conf = ToolConfDict(config_dict)

# Insert keys into the config
tool_conf.set_private_key(issuer, private_key_pem, client_id=client_id)
tool_conf.set_public_key(issuer, public_key_pem, client_id=client_id)

# Helper: Use Cookies + Cache for storing launch data
def _get_launch_data_storage():
    return CacheDataStorage(CookieService())

# LTI Endpoints
@lti_bp.route("/lti/jwks", methods=["GET"])
def lti_jwks():
    """
    Canvas calls this endpoint to get your public JWKS.
    """
    try:
        jwks = tool_conf.get_jwks(issuer, client_id)
        return jsonify(jwks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@lti_bp.route("/lti/login_initiation", methods=["GET"])
def lti_login_initiation():
    """
    OpenID Connect login initiation. Canvas hits this first.
    """
    try:
        iss = request.args.get("iss")
        req_client_id = request.args.get("client_id")
        if not iss or not req_client_id:
            raise LtiException("Missing iss or client_id in query params.")

        reg = Registration(tool_conf, iss)
        auth_login_url = reg.get_auth_login_url()
        launch_url = url_for("lti_bp.lti_launch", _external=True)

        oidc_login = reg.get_oidc_login(auth_login_url, launch_url)
        oidc_login.set_launch_data_storage(_get_launch_data_storage())
        return oidc_login.redirect()
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@lti_bp.route("/lti/launch", methods=["POST", "GET"])
def lti_launch():
    """
    Final LTI ResourceLinkRequest. Validate it, store any needed data, then show your UI.
    """
    try:
        iss = request.args.get("iss") or request.form.get("iss")
        if not iss:
            raise LtiException("No issuer (iss) in LTI launch.")

        message_launch = MessageLaunch(tool_conf, request, iss, _get_launch_data_storage())
        message_launch = message_launch.validate_registration().validate_deployment()

        # If needed, stores launch data in session
        launch_data = message_launch.get_launch_data()
        session["lti_launch_data"] = launch_data

        # Redirect to main UI
        return redirect("https://gator-aide-client.onrender.com")

    except Exception as e:
        return jsonify({"error": str(e)}), 400
