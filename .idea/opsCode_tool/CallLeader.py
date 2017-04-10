#!/usr/local/easyops/python/bin/python
# -*- coding: utf-8 -*-
#
# Author: Turing Chu
# Date: 2016-11-01 10:11:00
# File: sendNotice.py
#
# Description:
"""
"""

# std
import json
import re

# third
import requests


class Notice:

    def __init__(self, org=None, cmdb_ip=None):
        self.__org = org
        self.__user = "easyops"
        self.__host = "cmdb.easyops-only.com"
        self.__ip = cmdb_ip
        self.__headers = {
            "Host": self.__host,
            "org": self.__org,
            "user": self.__user,
            "Content-Type": "application/json"
        }

    def check_param(self, org, cmdb_ip):
        """
        检测org cmdb_ip是否合法
        :return: {"status":0, "msg":"success"}
        """
        result = {
            "status":0,
            "msg":"success"
        }
        match = re.match("^[1-9][0-9]*$", str(org))
        if not match:
            result["status"] = -1
            result["msg"] = "Invalid parameter, org: %s" % str(org)
            return result
        match = re.match("^((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(:\d+)?$", str(cmdb_ip))
        if not match:
            result["status"] = -1
            result["msg"] = "Invalid parameter, cmdb_ip: %s" % str(cmdb_ip)
            return result
        return result

    def get_app_info(self, app_id=None):
        """
        获取应用信息信息
        :param app_id:
        :return: {"status":0, "data":None, "msg":"success"}
        """
        result = {
            "status": 0,
            "data": None,
            "msg": "success"
        }
        url = "http://%s/app/%s" % (self.__ip, app_id)
        try:
            ret = requests.get(url=url, headers=self.__headers)
        except requests.exceptions.ConnectionError as ce:
            result["status"] = -1
            result["msg"] = ce
            return result
        if 200 != ret.status_code or 0 != json.loads(ret.content)["code"]:
            result["status"] = ret.status_code
            result["msg"] = ret.content
        else:
            result["status"] = 0
            result["data"] = json.loads(ret.content)["data"]
            result["msg"] = "success"
        return result

    def get_user_info(self, user_name=None):
        """
        用于获取对应人员邮箱列表
        :param user_name: 用户名
        :return: {"status": code, "data":None, "msg":"success"}
        """
        result = {
            "status": 0,
            "data": None,
            "msg": "success"
        }
        url = "http://%s/user/info/%s" % (self.__ip, user_name)
        ret = requests.get(url=url, headers=self.__headers)
        if 200 != ret.status_code or 0 != json.loads(ret.content)["code"]:
            result["status"] = ret.status_code
            result["msg"] = ret.content
        else:
            result["status"] = 0
            result["data"] = json.loads(ret.content)["data"]
            result["msg"] = "success"
        return result

        pass

    def send_notice(self, sendto=list(), subject="notice", msg=""):
        """
        发送通知
        :param sendto: 目标邮箱列表
        :param subject: 主题
        :param msg: 消息
        :return: {"status": code, "msg": ""}
        """
        result = {
            "status": 0,
            "msg": "success"
        }
        url = "http://%s/message/email" % self.__ip
        data = {
            "sendTo": ";".join(sendto),
            "subject": subject,
            "msg": msg
        }

        ret = requests.post(url, json=data, headers=self.__headers)
        if 200 != ret.status_code or 0 != json.loads(ret.content)["code"]:
            result["status"] = ret.status_code
            result["msg"] = ret.content if 500 != ret.status_code else "[ ERROR ] 发送邮件失败,请确认CMDB中邮件配置是否正确"
        else:
            result["status"] = 0
            result["msg"] = ret.content
        return result

if __name__ == "__main__":
    app_id = APP_ID
    cmdb_ip = EASYOPS_CMDB_HOST
    org = EASYOPS_ORG
    message = MESSAGE
    notice = Notice(org=org, cmdb_ip=cmdb_ip)
    ret = notice.check_param(org, cmdb_ip)
    if 0 != ret["status"]:
        PutStr("STATUS", str(ret["status"]))
        PutStr("MESSAGE", str(ret["msg"]))
        print ret["msg"]
        exit(ret["status"])
    ret = notice.get_app_info(app_id)
    if ret["status"] != 0:
        PutStr("STATUS", str(ret["status"]))
        PutStr("MESSAGE", str(ret["msg"]))
        print ret["msg"]
        exit(ret["status"])
    app_info = ret["data"]
    owner_emails = list()
    for owner in app_info["owner"]:
        owner_emails.append(notice.get_user_info(owner["name"])["data"]["user_email"])

    ret = notice.send_notice(sendto=owner_emails, subject="部署流水线结果", msg=message)
    if ret["status"] != 0:
        PutStr("STATUS", str(ret["status"]))
        PutStr("MESSAGE", str(ret["msg"]))
        print ret["msg"]
        exit(ret["status"])
    PutStr("STATUS", str(ret["status"]))
    PutStr("MESSAGE", str(ret["msg"]))
    print ret["msg"]