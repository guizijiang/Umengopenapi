#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import time
import json
import datetime
import requests
import codecs

GOAL_EVENTS = {}


class CallAPI(object):
    def __init__(self):
        self.baseurl = "http://api.umeng.com/"
        self.email = "aaa@test.com"
        self.password = "bbbb"

    def post_api(self, url, data):
        headers = {'content-type': 'application/json'}
        res = requests.post(url, data=json.dumps(data), timeout=60, headers=headers)
        return res.json()

    def get_api(self, url, auth=None):
        headers = {'content-type': 'application/json'}
        time.sleep(1)
        res = requests.get(url, params=auth, timeout=60, headers=headers)
        return res.json()

    def auth(self):
        data = {
            "email": self.email,
            "password": self.password,
        }
        url = self.baseurl + 'authorize'
        res = self.post_api(url, data)
        if res.get("auth_token"):
            return res["auth_token"]
        else:
            print("用户名或密码错误")
            return None

    def get_apps(self):
        auth = self.auth()
        data = {"auth_token": auth}
        url = self.baseurl + 'apps'
        res = self.get_api(url, data)
        apps = {}
        for app in res:
            apps.update({app.get("appkey"): app.get("name")})
        return apps

    def getdates(self, start_date_str, end_date_str):
        datelist = []
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        temp_date = start_date
        while temp_date < end_date:
            datelist.append(temp_date.strftime("%Y-%m-%d"))
            temp_date = temp_date + datetime.timedelta(days=1)
            continue
        datelist.append(end_date_str)
        return datelist

    def getchannels(self):
        auth = self.auth()
        data = {"auth_token": auth, "per_page": 100}
        url = self.baseurl + 'channels'
        appkeys = self.get_apps()
        appchannel = {}
        for appkey, appname in appkeys.items():
            data.update({"appkey": appkey})
            res = self.get_api(url, data)
            channels = {}
            for channel in res:
                channelid = channel.get("id")
                channelname = channel.get("channel")
                channels.update({channelid: channelname})
            appchannel.update({appkey: channels})
        return appchannel

    def get_eventgroup(self, start_date='', end_date=''):
        """获取三个app的事件对应的group_id"""
        appkey_groupids = {}
        auth = self.auth()
        data = {"auth_token": auth,
                "start_date": start_date,
                "end_date": end_date,
                "period_type": "daily"
                }
        url = self.baseurl + '/events/group_list'
        appkeys = self.get_apps()
        for app in appkeys.keys():
            groupid = []
            data.update({"appkey": app})
            res = self.get_api(url, data)
            for event_group in res:
                group_name = event_group.get("name")
                if group_name in GOAL_EVENTS.keys():
                    # groupid.append(event_group.get("group_id"))
                    groupid.append(event_group)
            appkey_groupids.update({app: groupid})
        return appkey_groupids

    def getchannelinstalls(self, start_date, end_date):
        auth = self.auth()
        data = {"auth_token": auth, "per_page": 100}
        url = self.baseurl + 'channels'
        appkeys = self.get_apps()
        datelist = self.getdates(start_date, end_date)
        f = codecs.open("channels.txt", "w", 'utf-8')
        f.write("appname" + "\t" + "channel" + "\t" + "installcount" + "\t" + "installdate" + "\n")
        for appkey, appname in appkeys.items():
            data.update({"appkey": appkey})
            for datestr in datelist:
                data.update({"date": datestr})
                # print("===========================================")
                # print(data)
                res = self.get_api(url, data)
                #print("++++++++++++++++++++++++++++++++++++++++++++")
                channels = {}
                for channel in res:
                    channelid = channel.get("id")
                    channelname = channel.get("channel")
                    channels.update({channelid: channelname})
                    channelname = channel.get("channel")
                    install = channel.get("install")
                    installdate = channel.get("date")
                    f.write(appname + "\t" + channelname + "\t" + str(install) + "\t" + installdate + "\n")
        f.close()

    def get_users(self, start_date='', end_date=''):
        """获取最终数据"""
        print("Start get data.................")
        apppchannels = self.getchannels()
        events = self.get_eventgroup(start_date=start_date, end_date=end_date)
        auth = self.auth()
        data = {"type": "device",
                "start_date": start_date,
                "end_date": end_date,
                "period_type": "daily",
                "group_id": "",
                "channels": "",
                "appkey": "",
                "auth_token": auth}
        url = self.baseurl + 'events/daily_data'
        apps = self.get_apps()
        filename = "userdata.txt"
        f = codecs.open(filename, "w", 'utf-8')
        f.write("appname" + "\t" + "channelname" + "\t" + "display_name" + "\t"
                + "event_id" + "\t" + "date" + "\t" + "usercount" + "\n")

        for appkey, channels in apppchannels.items():
            data["appkey"] = appkey
            appname = apps.get(appkey)
            for channelid, channelname in channels.items():
                data["channels"] = channelid
                for group in events.get(appkey):
                    group_id = group.get("group_id")
                    data["group_id"] = group_id
                    # print("===========================================")
                    # print(data)
                    res = self.get_api(url, data)
                    # print("++++++++++++++++++++++++++++++++++++++++++++")
                    userdata = res.get("data")
                    dates = res.get("dates")
                    users = userdata.get("all")
                    for index, date in enumerate(dates):
                        tempdata = {"app": appname, "channel": channelname,
                                    "display_name": group.get("display_name"), "name": group.get("name")
                                    }
                        tempdata.update({"date": date, "usercount": users[index]})
                        f.write(appname + "\t" + channelname + "\t" + group.get("display_name") + "\t"
                                + group.get("name") + "\t" + date + "\t" + str(users[index]) + "\n")

        f.close()
        print("Finish get data.................")


        # def get_events(self, start_date='2016-8-4', end_date='2016-8-11'):
        #     """获取三个app的事件列表"""
        #     auth = self.auth()
        #     data = {"start_date": start_date,
        #             "end_date": end_date,
        #             "period_type": "daily",
        #             "auth_token": auth}
        #     url = self.baseurl + '/events/event_list'
        #     event_groups = self.get_eventgroup()
        #     events = {}
        #     for app, groupids in event_groups.items():
        #         events_bygroup = []
        #         for groupid in groupids:
        #             data.update({"appkey": app,
        #                          "group_id": groupid
        #                          })
        #             res = self.get_api(url, data)
        #             for event in res:
        #                 event_id = event.get("event_id")
        #                 events_bygroup.append(event_id)
        #         events.update({app: events_bygroup})
        #     return events


if __name__ == "__main__":
    # umeng = CallAPI()
    # umeng.getdates('2016-08-01', '2016-08-12')

    if len(sys.argv) == 2:
        if sys.argv[1] == "monthly":
            print("将获取最近一月的数据")
            end_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            start_date = time.strftime('%Y-%m-%d', time.localtime(time.time() - 30 * 24 * 3600))
        else:
            print("你输入的参数不正确")
            sys.exit()
    elif len(sys.argv) == 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        print("您没有输入参数，将获取最近一周的数据")
        end_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        start_date = time.strftime('%Y-%m-%d', time.localtime(time.time() - 7 * 24 * 3600))
    # 2016-08-05 2016-08-08
    umeng = CallAPI()
    umeng.getchannelinstalls(start_date, end_date)
    # umeng.get_users(start_date=start_date, end_date=end_date)
