from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask.wrappers import Response
from logging import info

from eNMS.controller import controller
from eNMS.modules import bp, db


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.get_route"), endpoint="login")


@bp.route("/<endpoint>", methods=["GET"])
@login_required
def get_route(endpoint: str) -> Response:
    func, *args = endpoint.split("-")
    ctx = getattr(controller, func)(*args) or {}
    if not isinstance(ctx, dict):
        return ctx
    ctx["endpoint"] = endpoint
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f"calling the endpoint {endpoint} (GET)"
    )
    if func == "filtering":
        return jsonify(ctx)
    return render_template(f"{ctx.pop('template', 'pages/' + endpoint)}.html", **ctx)


@bp.route("/<endpoint>", methods=["POST"])
@login_required
def post_route(endpoint: str) -> Response:
    data = {**request.form.to_dict(), **{"creator": current_user.id}}
    for property in data.get("list_fields", "").split(","):
        data[property] = request.form.getlist(property)
    for property in data.get("boolean_fields", "").split(","):
        data[property] = property in request.form
    request.form = data
    func, *args = endpoint.split("-")
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f" calling the endpoint {request.url} (POST)"
    )
    try:
        result = getattr(controller, func)(*args)
        db.session.commit()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})
