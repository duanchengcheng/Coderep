# -*- coding: utf-8 -*-

import urllib2
import urllib
import json
import time
import traceback
import sys

HTTP_OK = 0
URL_ERROR = -1
UNKNOWN_ERROR = -2


headers = {'org': EASYOPS_ORG, "Host": "command.easyops-only.com", "user": "defaultUser", "Content-Type": "application/json"}
send_command_url = 'http://{ip}/cmd'.format(ip=EASYOPS_COMMAND_HOST, port=8060)
check_command_url = 'http://{ip}/cmd/detail/'.format(ip=EASYOPS_COMMAND_HOST, port=8060)


params = {
    "name": "test1",
    "type": "command",
    "groupId": "abcdefg",
    "callback": {
        "url": "http://www.linus.com/",
        "ip": "",
        "port": 10000
    },
    "actions": [
        {
            "name": "actName12",
            "type": "cmd",
            "action": "runCmd",
            "param": {
                "timeout": 3600*10,
                "cmd": "df",
                "execUser": "root",
                "scriptType":"shell",
                "parser":"/bin/bash"
            }
        },
    ],
    "targets": [
    ]
}


def check_disk_free(ret_str):
    lines = ret_str.split("\n")
    if len(lines) < 2:
        return False
    index_list = lines[0].split()
    index = 0
    for idx, each in enumerate(index_list):
        if each.lower() == "use%":
            index = idx
            break
    if index == 0:
        return False, "df command not expected"
    for line in lines[1:]:
        infos = line.split()
        if len(infos) < index + 1:
            continue
        use_percent = infos[index]
        if use_percent.find("100") == 0:
            return False, "one disk is 100% used, please check"
    return True, ""


def send_command(ip, cmd):
    params["actions"][0]["param"]["cmd"] = cmd
    params["targets"] = [{"targetId": ip, "channel": "agent"}]
    ret_code, data = do_http("POST", send_command_url, params, headers)
    task_id = data['data']['taskId']
    check_params = {'taskId': task_id}

    ret_flag, ret_logs = check_command_result(check_params, [ip])
    if not ret_flag:
        return False, ""
    if ip in ret_logs:
        target_ret = ret_logs[ip]
        return True, target_ret
    else:
        return False, ""


def check_command_result(params, targets=[]):
    time_begin = int(time.time())
    ret_logs = {}
    url = check_command_url + params['taskId']
    while True:
        time.sleep(1)
        ret_code, data = do_http("GET", url, {}, headers)
        if not ret_code:
            continue
        if data['code'] != 0:
            return False, ret_logs
        if data["data"]["status"] == "failed":
            targets_log = data["data"]["targetsLog"]
            for target_ip in targets:
                for target_log in targets_log:
                    if target_log["targetId"] == target_ip:
                        action_log = target_log["actionsLog"][0]['msg']
                        #print type(action_log)
                        try:
                            ret_logs[target_ip] = json.loads(action_log)
                        except Exception, e:
                            return False, e
            return False, ret_logs
        elif data["data"]["status"] == "ok":
            targets_log = data["data"]["targetsLog"]
            for target_ip in targets:
                for target_log in targets_log:
                    if target_log["targetId"] == target_ip:
                        action_log = target_log["actionsLog"][0]['msg']
                        ret_logs[target_ip] = action_log
            return True, ret_logs
        else:
            continue


def do_http(method, url, params={}, headers={}, timeout=60):
    """
    do http request
    """
    try:
        method = method.upper()
        if not isinstance(params, dict) or not isinstance(headers, dict):
            raise Exception('params and headers must be dict')
        if len(params) > 0:
            if method == 'GET':
                data = urllib.urlencode(params)
                if '?' not in url:
                    url = '%s?%s' %(url, data)
                else:
                    url = '%s&%s' %(url, data)
                request = urllib2.Request(url)
            else:
                if headers.get('Content-Type', '').lower() == 'application/json':
                    data = json.dumps(params)
                else:
                    data = urllib.urlencode(params)
                request = urllib2.Request(url, data=data)
        else:
            request = urllib2.Request(url)
        for key, val in headers.items():
            request.add_header(key, val)
        request.get_method = lambda: method
        response = urllib2.urlopen(request, timeout=timeout)

        data = response.read()
        response.close()
        return True, json.loads(data)
    except Exception, e:
        print e
        return False, e.__str__()


if __name__ == "__main__":
    #ip_list = ["192.168.100.162", "192.168.100.64"]
    #print EASYOPS_COMMAND_HOST
    #print EASYOPS_ORG
    ip_list = IP_LIST.split(",")
    try:
        check_free_cmd = 'df -h'
        for ip in ip_list:
            ret, ret_str = send_command(ip, check_free_cmd)
            if not ret:
                info = ip, " not online"
                print info
                PutRow("pre_check_env", "host={ip}&message={msg}".format(ip=ip, msg=info))
                exit(1)
            ret, ret_str = check_disk_free(ret_str)
            if not ret:
                print ret, ret_str
                PutRow("pre_check_env", "host={ip}&message={msg}".format(ip=ip, msg=ret_str))
                exit(1)
            PutRow("pre_check_env", "host={ip}&message={msg}".format(ip=ip, msg="`df` command check ok"))
    except Exception, e:
        print traceback.format_exc()