# import mongoengine as me
# import datetime


# class Datetime(me.EmbeddedDocument):
#     year = me.StringField(required=True, default="")
#     month = me.StringField(required=True, default="")
#     start_date = me.StringField(required=True, default="")
#     end_date = me.StringField(required=True, default="")

# class Table_Downtime(me.EmbeddedDocument):
#     host_name = me.StringField(required=True, default="")
#     sum_downtime = me.IntField(required=True, default="")
#     sum_duration = me.DateTimeField(required=True, default="")
#     Uptime_pm = me.FloatField(required=True, default="")

# class Events(me.EmbeddedDocument):
#     year = me.StringField(required=True, default="")
#     month = me.StringField(required=True, default="")
#     eventid = me.StringField(required=True, default="")
#     date_down = me.StringField(required=True, default="")  # แปลงจาก clock
#     date_up = me.StringField(required=True, default="") # แปลงจาก r_eventid
#     duration = me.StringField(required=True, default="") # คิดจาก date_up - date_down
#     downtime_cause = me.StringField(required=True, default="")

# class Group_Host(me.Document):
#     meta = {"collection": "group_host"}
#     group_id = me.StringField(required=True, default="")
#     group_name = me.StringField(required=True, default="")
#     check_date = me.ListField(me.EmbeddedDocumentField(Datetime))

# class Host(me.Document):
#     meta = {"collection": "host"}
#     host_id = me.StringField(required=True, default="")
#     host_name = me.StringField(required=True, default="")
#     description = me.StringField(required=True, default="")
#     events = me.ListField(me.EmbeddedDocumentField(Events))

# class Downtime(me.Document):
#     meta = {"collection": "downtime"}
#     date = me.DictField(required=True, unique=True , default="") # เก็บ year และ month
#     downtime = me.IntField(required=True, default="")
#     d_downtime = me.DictField(required=True, default="")
#     t_downtime = me.ListField(me.EmbeddedDocumentField(Table_Downtime))
#     status_kpi = me.StringField(required=True, default="")
