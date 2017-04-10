#!/usr/local/easyops/python/bin/python
# -*- coding: utf-8 -*-

"""
上传程序包文件到平台

input params:
APP_ID: 应用id
PACKAGE_ID: 程序包id
git_tag_name: 默认git_tag作为版本号
PACKAGE_PATH: 上一步打包的文件路径

output params:


退出错误码：
1. 参数不足
2. 应用不存在
3. 应用下没有程序包
4. 指定程序包不存在
5. 版本已经存在
6. 指定路径下没有文件
7. 上传文件失败
8. 创建版本失败
9. 清空工作空间失败
"""


import os
# import json
import logging
import requests


FORMAT = "[line %(lineno)d-%(levelname)s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("log")
logger.setLevel(logging.DEBUG)

cmdb_header = "cmdb.easyops-only.com"
deploy_header = "deploy.easyops-only.com"
deployrepo_header = "deployrepo.easyops-only.com"

headers = {
    "org": EASYOPS_ORG,
    "user": "defaultUser",
    "Host": ""
}


def get_app(app_name):
    """
    获取应用信息
    """
    url = "http://%s/object/instance/list/APP" % EASYOPS_CMDB_HOST
    headers["Host"] = cmdb_header

    res = requests.get(url, headers=headers)

    app = {}
    recs = res.json()["data"].get("list", [])

    for rec in recs:
        if app_id == rec["appId"]:
            app["name"] = rec["name"]
            app["appId"] = rec["appId"]
            app["_packageList"] = rec["_packageList"] or []
            break

    if not app:
        logger.warn(u"平台上没有这个应用: %s, 请检查！"  % app_id)
        exit(2)
    return app


def get_package(package_id):
    """
    获取包信息
    """
    url = "http://%s/package/%s" % (EASYOPS_DEPLOY_HOST, package_id)
    headers["Host"] = deploy_header

    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        return resp.json()["data"]

    return {}


def get_package_versions(package_id):
    """
    获取包版本列表
    """
    url = "http://%s/version/list" % EASYOPS_DEPLOY_HOST
    params = {
        "page": 1,
        "pageSize": 200,
        "packageId": package_id,
        "order": "ctime desc"
    }
    headers["Host"] = deploy_header

    res = requests.get(url, params=params, headers=headers)

    if res.status_code == 200:
        return res.json()["data"]["list"]

    return {}


def get_package_files_list(package_id):
    """
    获取包文件列表
    """
    url = "http://%s/package/files" % EASYOPS_DEPLOY_HOST
    params = {
        'packageId': package_id,
        'path': '/',
    }
    headers["Host"] = deploy_header

    res = requests.get(url, params=params, headers=headers)
    if res.status_code == 200:
        return res.json()["data"]

    return []


def clear_workspace(package_id):
    url = "http://%s/workspace/%s" % (EASYOPS_DEPLOY_HOST, package_id)
    headers["Host"] = deployrepo_header

    res = requests.delete(url, headers=headers)
    if res.status_code == 200:
        logger.info(u'workspace已经清空')
    else:
        logger.info(u'清理workspace失败')
        exit(9)


def upload_file(package_id, package_path, clear_first=True):
    """
    上传文件
    """
    if clear_first:
        logger.info(u'开始清理 workspace ...')
        clear_workspace(package_id)

    url = "http://%s/archive" % EASYOPS_DEPLOY_REPO_HOST
    file_path = os.path.join(package_path)
    if os.path.isfile(file_path):
        files = {"file": open(file_path, "rb")}
    else:
        logger.warn(u"指定目录下: %s 未找到文件" % file_path)
        exit(6)

    data = {
        "unzip": "true",
        "stripFirst": "true",
        "packageId": package_id,
        "message": "auto package"
    }
    headers["Host"] = deployrepo_header

    ret = requests.post(url, files=files, data=data, headers=headers)
    if ret.status_code == 200:
        logger.info(u'文件上传成功')
        version_id = ret.json()['data']['id']
        sign = ret.json()['data']['sign']
        return version_id, sign
    else:
        logger.warn(u'上传文件失败')
        exit(7)


def create_new_version(package_id, git_tag, version_id, sign):
    """
    创建新版本
    """
    url = "http://%s/version/sign" % EASYOPS_DEPLOY_HOST
    params_dict = {
        "packageId": package_id,
        "versionId": version_id,
        "name": git_tag,
        "memo": "auto package",
        "sign": sign,
        "source": {
            "type": "http",
            "host": "deployrepo.easyops-only.com",
            "ip": EASYOPS_DEPLOY_REPO_HOST,
            "port": 80,
            "ensName": "logic.deploy.repo.archive",
        },
    }
    headers["Host"] = deploy_header
    headers["content-type"] = "application/json"

    res = requests.post(url, json=params_dict, headers=headers)

    if res.status_code == 200:
        return res.json()["data"]

    return {}


def main(app_id, package_id, git_tag, package_path, clear_first=True):
    app = get_app(app_id)
    if app["_packageList"]:
        logger.info(u'找到指定的应用: %s' % app['name'])
        package_exist = False
        for package_ids in app["_packageList"]:
            if package_id == package_ids["packageId"]:
                package = get_package(package_id)
                package_exist = True
                logger.info(u'找到指定的包: %s' % package['name'])
                break

        if package_exist:
            package_versions = get_package_versions(package_id)
        else:
            logger.warn(u"指定的包不存在，它的包id 是: %s" % package_id)
            exit(4)

        for package_version in package_versions:
            if git_tag == package_version["name"]:
                logger.warn(u"版本: %s 已经存在，请检查" % git_tag)
                exit(5)

        version_id, sign = upload_file(package_id, package_path)
        new_version = create_new_version(package_id, git_tag, version_id, sign)
        if not new_version:
            logger.warn(u'创建版本失败！')
            exit(8)
        else:
            logger.info(u'创建版本成功！')

    else:
        logger.warn(u"应用: %s下面没有绑定包" % app_id)
        exit(3)


if __name__ == "__main__":
    app_id = APP_ID
    package_id = PACKAGE_ID
    git_tag = version
    package_path = PACKAGE_PATH
    print app_id, package_id, git_tag, package_path
    if app_id and package_id and git_tag and package_path:
        main(app_id, package_id, git_tag, package_path, clear_first=True)
    else:
        logger.warn(u'参数不足')
        exit(1)