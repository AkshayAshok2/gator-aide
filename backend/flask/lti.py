import json
import logging
import os

from flask import request, session, jsonify
from pylti1p3.tool_config import ToolConfDict
from pylti1p3.contrib.flask import (
    FlaskCookieService,
    FlaskMessageLaunch,
    FlaskOIDCLogin,
    FlaskRequest,
    FlaskCacheDataStorage
)


private_key_pem = os.environ.get("LTI_PRIVATE_KEY", "")
public_key_pem = os.environ.get("LTI_PUBLIC_KEY", "")
if not private_key_pem or not public_key_pem:
    raise RuntimeError("Missing LTI_PRIVATE_KEY or LTI_PUBLIC_KEY in environment!")
 
issuer = "https://canvas.instructure.com"
client_id = os.environ.get("LTI_CLIENT_ID")
deployment_id = os.environ.get("LTI_DEPLOYMENT_ID", "")

pylti_config_dict = {
    issuer: [
        {
            "default": True,
            "client_id": client_id,
            "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
            "auth_token_url": "https://sso.canvaslms.com/login/oauth2/token",
            "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
            "deployment_ids": [deployment_id]
        }
    ]
}

tool_conf = ToolConfDict(pylti_config_dict)
tool_conf.set_private_key(issuer, private_key_pem, client_id=client_id)
tool_conf.set_public_key(issuer, public_key_pem, client_id=client_id)

def get_jwks():
    # Fetch the public JWKS from tool_conf.
    jwks = tool_conf.get_jwks(issuer, client_id)
    return jsonify(jwks)

def tool_login(launch_data_storage):
    wrapped_flask_request = FlaskRequest(
        cookies=request.cookies,
        session=session
    )
    # target_link_uri = wrapped_flask_request.get_param("target_link_uri")
    target_link_uri = "https://gator-aide-fubd.onrender.com/lti/login_initiation"

    if not target_link_uri:
        return jsonify({"error": "Missing target_link_uri"}), 400
    cookie_service = FlaskCookieService(wrapped_flask_request)

    return FlaskOIDCLogin(
        request=wrapped_flask_request,
        tool_config=tool_conf,
        launch_data_storage=launch_data_storage,
        cookie_service=cookie_service
    ).enable_check_cookies().redirect(target_link_uri)


def setup_lti_session(launch_data_storage):
    """
    Retrieves the message_launch and returns it.

    :param launch_id: The original launch_id.
    :param request: The flask request.

    :returns: The message_launch.
    :rtpes: MessageLaunch
    """
    wrapped_flask_request = FlaskRequest(
        cookies=request.cookies,
        session=session
    )
    message_launch = FlaskMessageLaunch(
        request=wrapped_flask_request,
        tool_config=tool_conf,
        launch_data_storage=launch_data_storage
    )

    # Cache the public key for the LMS.
    message_launch.set_public_key_caching(
        launch_data_storage, cache_lifetime=7200)

    launch_data = message_launch.get_launch_data()

    cookie_service = FlaskCookieService(wrapped_flask_request)
    cookie_service.set_cookie("launch_id", message_launch.get_launch_id())

    # user_id = launch_data.get("https://purl.imsglobal.org/spec/lti/claim/lti1p1").get("user_id")
    # roles = launch_data.get("https://purl.imsglobal.org/spec/lti/claim/roles")
    # context_id = launch_data.get("https://purl.imsglobal.org/spec/lti/claim/context").get("id")
    # resource_id = launch_data.get("https://purl.imsglobal.org/spec/lti/claim/resource_link").get("id")

    return launch_data, cookie_service

def get_launch_data_storage(cache):
    """
    Returns the launch data storage.

    :params: None

    :return: The launch data storage.
    :rtype: FlaskCacheDataStorage
    """

    return FlaskCacheDataStorage(cache)

# import os, logging
# from flask import Blueprint, jsonify, redirect, session, request, url_for
# from dotenv import load_dotenv
# from backend.flask.index import cache 
# from pylti1p3.contrib.flask import (
#     FlaskRequest, 
#     FlaskOIDCLogin, 
#     FlaskMessageLaunch, 
#     FlaskSessionService, 
#     FlaskCookieService,
#     FlaskCacheDataStorage
# )

# from pylti1p3.tool_config import ToolConfDict
# from pylti1p3.exception import LtiException

# lti_bp = Blueprint("lti_bp", __name__)

# load_dotenv()

# # Set up config
# private_key_pem = os.environ.get("LTI_PRIVATE_KEY", "")
# public_key_pem = os.environ.get("LTI_PUBLIC_KEY", "")
# if not private_key_pem or not public_key_pem:
#     raise RuntimeError("Missing LTI_PRIVATE_KEY or LTI_PUBLIC_KEY in environment!")
 
# issuer = "https://canvas.instructure.com"
# client_id = os.environ.get("LTI_CLIENT_ID")
# deployment_id = os.environ.get("LTI_DEPLOYMENT_ID", "")

# pylti_config_dict = {
#     issuer: [
#         {
#             "default": True,
#             "client_id": client_id,
#             "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
#             "auth_token_url": "https://sso.canvaslms.com/login/oauth2/token",
#             "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
#             "deployment_ids": [deployment_id]
#         }
#     ]
# }

# tool_conf = ToolConfDict(pylti_config_dict)
# tool_conf.set_private_key(issuer, private_key_pem, client_id=client_id)
# tool_conf.set_public_key(issuer, public_key_pem, client_id=client_id)

# class ExtendedFlaskMessageLaunch(FlaskMessageLaunch):

#     def validate_nonce(self):
#         """
#         Probably it is bug on "https://lti-ri.imsglobal.org":
#         site passes invalid "nonce" value during deep links launch.
#         Because of this in case of iss == http://imsglobal.org just skip nonce validation.

#         """
#         iss = self.get_iss()
#         deep_link_launch = self.is_deep_link_launch()
#         if iss == "http://imsglobal.org" and deep_link_launch:
#             return self
#         return super().validate_nonce()


# def get_launch_data_storage():
#     return FlaskCacheDataStorage(cache)

# # JWKS ENDPOINT
# @lti_bp.route("/lti/jwks", methods=["GET"])
# def lti_jwks():
#     try:
#         # Fetch the public JWKS from tool_conf.
#         jwks = tool_conf.get_jwks(issuer, client_id)
#         return jsonify(jwks)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
# # LOGIN INITIATION (OIDC)
# @lti_bp.route("/lti/login_initiation", methods=["GET", "POST"])
# def lti_login_initiation():
#     try:
#         flask_request = FlaskRequest()
#         launch_data_storage = get_launch_data_storage() 
        
#         target_link = flask_request.get_param("target_link_uri")
#         if not target_link:
#             return jsonify({"error": "Missing target_link_uri"}), 400

#         oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=launch_data_storage)
#         return oidc_login\
#         .enable_check_cookies()\
#         .redirect(target_link)

#     except LtiException as e:
#         return jsonify({"error": f"LTI error: {str(e)}"}), 400
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # LTI LAUNCH
# @lti_bp.route("/lti/launch", methods=["GET", "POST"])
# def lti_launch():
#     try:
#         # Use FlaskRequest, launch data storage, and ExtendedFlaskMessageLaunch
#         flask_request = FlaskRequest()
#         launch_data_storage = get_launch_data_storage()
#         message_launch = ExtendedFlaskMessageLaunch(flask_request, tool_conf, launch_data_storage=launch_data_storage)
#         message_launch_data = message_launch.get_launch_data()

#         # Debugging output (prints launch data for verification)
#         pprint.pprint(message_launch_data)

#         # Store the launch data in session
#         session["lti_launch_data"] = message_launch_data

#         # Redirect to main UI (unchanged from your original implementation)
#         return redirect("https://gator-aide-fubd.onrender.com")

#     except LtiException as e:
#         return jsonify({"error": f"LTI error: {str(e)}"}), 400
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    
# # # LOGIN INITIATION (OIDC)
# # @lti_bp.route("/lti/login_initiation", methods=["GET", "POST"])
# # def lti_login_initiation():
# #     try:
# #         flask_request = FlaskRequest()

# #         oidc_login = FlaskOIDCLogin(
# #             request=flask_request,
# #             tool_config=tool_conf,
# #             session_service=FlaskSessionService(flask_request),
# #             cookie_service=FlaskCookieService(flask_request)
# #         )

# #         logging.debug("LTI Login Initiation Request Params: %s", request.args.to_dict())

# #         # Debugging: Log request params
# #         logging.debug(f"LTI Login Initiation Request: {request.args.to_dict()}")

# #         # Check for missing target_link_uri
# #         target_link = flask_request.get_param("target_link_uri")
# #         if not target_link:
# #             logging.warning("Missing target_link_uri, using fallback")
# #             target_link = "https://gator-aide-fubd.onrender.com/lti/launch"  # Fallback

# #         logging.debug(f"Redirecting to target link: {target_link}")

# #         return oidc_login.redirect(target_link)

# #     except LtiException as e:
# #         return jsonify({"error": f"LTI error: {str(e)}"}), 400
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # # LTI LAUNCH
# # @lti_bp.route("/lti/launch", methods=["GET", "POST"])
# # def lti_launch():
# #     try:
# #         # Create a "FlaskRequest" for the LTI message
# #         flask_request = FlaskRequest()

# #         # Build a message launch object
# #         message_launch = FlaskMessageLaunch(
# #             request=flask_request,
# #             tool_config=tool_conf,
# #             session_service=FlaskSessionService(flask_request),
# #             cookie_service=FlaskCookieService(flask_request)
# #         )

# #         message_launch_data = message_launch.validate() 

# #         launch_data = message_launch.get_launch_data()
# #         session["lti_launch_data"] = launch_data

# #         # Redirect to main UI
# #         return redirect("https://gator-aide-fubd.onrender.com")

# #     except LtiException as e:
# #         return jsonify({"error": f"LTI error: {str(e)}"}), 400
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400