#!/usr/local/easyops/python/bin/python
# encoding: utf-8

import json
import logging
import requests

deploy_header = 'deploy.easyops-only.com'

FORMAT = '[line %(lineno)d-%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

headers = {
    'org': EASYOPS_ORG,
    'user': 'defaultUser',
    'Host': '',
}


def get_instance_version(package_id, device_id, device_ip, installed_version):
    """
    获取已安装的包的版本信息
    """
    url = 'http://%s/instance/search' % EASYOPS_DEPLOY_HOST
    headers['Host'] = deploy_header
    params = {
        'packageId': package_id,
        'deviceId': device_id,
        'deviceIp': device_ip,
        'page': 1,
        'pageSize': 1
    }

    res = requests.get(url, params=params, headers=headers)
    msg = ''
    fail = 0
    if res.status_code == 200:
        pkg_list = res.json()['data']['list']
        for pkg in pkg_list:
            if installed_version[device_ip] == pkg['versionName']:
                msg = u'部署成功！部署机器IP: %s, 程序包名: %s, 程序包版本: %s' % (pkg['deviceIp'], pkg['packageName'], pkg['versionName'])
                logger.info(msg)
    else:
        fail += 1
        msg = u'未能获取机器 %s 的安装版本: %s' % device_ip
        logger.error(msg)
    if fail:
        return "fail", msg
    return "success", msg.encode('utf-8')


def main(package_id, device_list, installed_version):
    device_list = json.loads(device_list)
    msg = []
    if device_list:
        for device in device_list:
            device_id = device['deviceId']
            device_ip = device['ip']
            status, info = get_instance_version(package_id, device_id, device_ip, installed_version)
            msg.append(info)
    else:
        logger.error(u"这个集群下没有设备！请检查")
        exit(1)
    return status, msg

if __name__ == "__main__":
    package_id = PACKAGE_ID
    device_list = DEVICE_LIST
    installed_version = INSTALLED_VERSION
    installed_version = json.loads(installed_version)
    status, info = main(package_id, device_list, installed_version)
    info = ' '.join(info)
    PutStr("STATUS", status)
    PutStr("MESSAGE", str(info))