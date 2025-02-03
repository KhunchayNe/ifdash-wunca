from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    Response,
    request,
)
from flask_login import login_required, current_user

from ifdash import models

import beanie

from .. import forms
from .. import caches

import datetime


module = Blueprint("equipments", __name__, url_prefix="/equipments")


@caches.cache.memoize(timeout=10 * 60)
def get_all_groups():
    now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=5)
    host_groups = models.beanie_client.loop.run_until_complete(
        models.HostState.distinct("metadata.groups", {"timestamp": {"$gt": now}})
    )
    ap_groups = models.beanie_client.loop.run_until_complete(
        models.APState.distinct("metadata.groups", {"timestamp": {"$gt": now}})
    )

    host_groups.extend(ap_groups)
    host_groups = set(host_groups)
    return host_groups


@caches.cache.memoize(timeout=10 * 60)
def get_hosts_by_group(group):
    pipelines = [
        {
            "$match": {
                "timestamp": {
                    "$gt": datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(days=2)
                },
                "metadata.groups": group,
            }
        },
        {
            "$group": {
                "_id": {
                    "id": "$metadata.id",
                    "name": "$metadata.name",
                    "host_name": "$metadata.host_name",
                }
            }
        },
    ]

    host_names = {}

    hosts = models.beanie_client.loop.run_until_complete(
        models.HostState.aggregate(pipelines).to_list()
    )
    aps = models.beanie_client.loop.run_until_complete(
        models.APState.aggregate(pipelines).to_list()
    )

    for host_infos in [hosts, aps]:
        for host_info in host_infos:
            if host_info["_id"]["id"] not in host_names:
                host_names[host_info["_id"]["id"]] = host_info["_id"]

    return host_names


@module.route("/")
@login_required
def index():
    host_groups = get_all_groups()
    return render_template("/equipments/index.html", host_groups=host_groups)


@module.route("/show/<group>", methods=["GET", "POST"])
@login_required
def show_hosts_in_group(group):
    equipments = models.beanie_client.loop.run_until_complete(
        models.Equipment.find().to_list()
    )

    hosts = get_hosts_by_group(group)
    remove_keys = []
    for equipment in equipments:
        for key, host in hosts.items():
            if key == equipment.host_id:
                remove_keys.append(key)
                break

    for key in remove_keys:
        hosts.pop(key)

    return render_template("/equipments/show.html", equipments=equipments, hosts=hosts)


@module.route("/update/<equipment_id>", methods=["GET", "POST"])
@login_required
def update(equipment_id):
    group = request.args.get("group")
    equipment = None
    try:
        equipment = models.beanie_client.loop.run_until_complete(
            models.Equipment.find_one(
                models.Equipment.id == beanie.PydanticObjectId(equipment_id)
            )
        )
    except Exception as e:
        print(e)

    if not equipment:

        equipment = models.beanie_client.loop.run_until_complete(
            models.Equipment.find_one(models.Equipment.host_id == equipment_id)
        )

    form = forms.equipments.EquipmentForm()
    if equipment:
        form.coordinates.data = equipment.coordinates.coordinates

    if not form.validate_on_submit():
        return render_template(
            "/equipments/update.html", form=form, equipment_id=equipment_id
        )

    if not equipment:
        equipment = models.Equipment(host_id=equipment_id)

    equipment.coordinates.coordinates = form.coordinates.data
    equipment.updated_date = datetime.datetime.now(datetime.timezone.utc)

    models.beanie_client.loop.run_until_complete(equipment.save())

    return redirect(url_for("equipments.show_hosts_in_group", group=group))
