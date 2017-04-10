#!/usr/local/easyops/python/bin/python
# -*- coding: utf-8 -*-
#
# Author: Turing Chu
# Date: 2016-11-01 16:27:00
# File: pkg_1.py
#
# Description:
"""
1 创建临时目录
2 复制文件
3 删除不必要的文件
4 生成版本号
5 生成package.conf.yaml
6 打包
"""

# std
import os
import time
import shutil
import tarfile

# third
import yaml

# global variable
PACKAGE_PATH = "/tmp/easyops/pkg"


def create_tmp_folder(app_name, src_dir=None):
    """
    创建临时目录
    :param src_dir: 源代码存放目录
    :return: {"status": code, "msg", "data"}
    """
    if not os.path.isdir(PACKAGE_PATH):
        os.makedirs(name=PACKAGE_PATH, mode=0o755)
    if not os.path.isdir(src_dir):
        msg = "not found %s, exit" % src_dir
        print msg
        return {"status": -1, "msg": msg, "data": None}
    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    tmp_folder = os.path.join(os.path.dirname(src_dir), app_name) + "." + timestamp

    if not os.path.isdir(tmp_folder):
        os.makedirs(name=tmp_folder, mode=0o755)
    return {
        "status": 0,
        "msg": "success",
        "data": tmp_folder
    }


def cp_file(app_name, src_dir, dest_dir):
    """
    将原文件复制到临时目录
    相当于 cp -r /a/b/c  /d/e/
    最后会是 /d/e/c
    :param src_dir:
    :param dest_dir:
    :return: {"status": code, "msg": "success", "data": None}
    """
    dest_dir = os.path.join(dest_dir, app_name)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.copytree(src=src_dir, dst=dest_dir)

    return {"status": 0, "msg": "success", "data": None}


def del_file(app_name, tmp_folder, filters=""):
    """
    删除不必要的文件 默认删除 .git .gitignore
    但要提供可选参数来过滤文件
    :param src_dir:
    :param tmp_folder:
    :param filters: string 要删除的文件列表 中间以空格分割
    :return: None
    """
    # 这里建议用集合
    if len(filters) == 0:
        filters = []
    else:
        filters = filters.split(" ")
    filters.append(".git")
    filters.append(".gitignore")
    chg_folder = os.path.join(tmp_folder, app_name)
    os.chdir(chg_folder)
    for f in filters:
        if os.path.exists(f):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)
        else:
            print "not found: %s" % str(f)


def make_version(tag=None, app_name=None, tmp_folder=None):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    ver_fd = open(os.path.join(tmp_folder, "%s/version.ini" % app_name), mode="a")
    ver_fd.write(timestamp + "\n")
    ver_fd.write(tag + "\n")


# package.conf.yaml文件部分 这里暂时使用easyops平台的方式, 后续会将这些启停脚本放到指定目录中
# 到时候再重构
##############################################################
class folded_unicode(unicode):
    pass


class literal_unicode(unicode):
    pass


def folded_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')

def literal_unicode_representer(dumper, data):
    # 经测试，如果有行尾空格的话，转换成yaml展示为多行，会变为double-quoted模式
    # 行头如果是tab分隔也会有问题
    # 不知是bug，还是规定 Alren 20160709
    data_rstrip = os.linesep.join([d.replace('\t', ' '*4).rstrip() for d in data.splitlines()])
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data_rstrip, style='|')

yaml.add_representer(folded_unicode, folded_unicode_representer)
yaml.add_representer(literal_unicode, literal_unicode_representer)


def get_pkg_conf_sample():
    """
    生成package.conf.yaml 模版
    :return:
    """
    return """
---
proc_list: []
port_list: []
start_script: ""
stop_script: ""
restart_script: ""
install_prescript: ""
install_postscript: ""
update_prescript: ""
update_postscript: ""
rollback_prescript: ""
monitor_script: ""
crontab: ""
clear_file: ""
proc_guard: none
port_guard: none
user: root:root
...
"""


def create_yaml(app_name, tmp_folder):
    """

    :param app_name:
    :param tmp_folder:
    :return: {"status": 0, "msg": "success", "data": None}
    """
    app_folder = os.path.join(tmp_folder, app_name)
    deploy_folder = os.path.join(app_folder, "deploy")
    dst_file = os.path.join(app_folder, "package.conf.yaml")

    # 优先从deploy目录load，如果没有则从程序一级目录load，如果还没有则load模板
    if os.path.exists(os.path.join(deploy_folder, "package.conf.yaml")):
        with open(os.path.join(deploy_folder, "package.conf.yaml")) as fp:
            conf = yaml.load(fp)
    elif os.path.exists(os.path.join(app_folder, "package.conf.yaml")):
        with open(os.path.join(app_folder, "package.conf.yaml")) as fp:
            conf = yaml.load(fp)
    else:
        conf = yaml.load(get_pkg_conf_sample())

    section_list = [
        "install_prescript",
        "install_postscript",
        "update_postscript",
        "update_prescript",
        "start_script",
        "stop_script",
        "monitor_script",
        "crontab",
        "clear_file"
    ]
    for section in section_list:
        script_file = os.path.join(deploy_folder, section + ".sh")
        if not os.path.exists(script_file):
            continue
        with open(script_file, "r") as fp:
            conf[section] = literal_unicode(fp.read().decode("'utf8'"))

    with open(dst_file, "w") as fp:
        yaml.dump(conf, fp, default_flow_style=False, allow_unicode=True)

    return {"status": 0, "msg": "success", "data": None}


# 打压缩包
#####################################################################
def make_tar(folder_to_dir, dst_folder="/", compression="gz"):
    """

    :param folder_to_dir: 要打包的文件夹的路径
    :param dst_folder: 压缩文件的存放路径
    :param compression: 压缩格式 gz bz2等
    :return:
    """
    #是否需要压缩
    if compression:
        dst_ext = compression
    else:
        dst_ext = ''

    dst_name = "%s.tar.%s" % (os.path.basename(folder_to_dir), dst_ext)
    dst_path = os.path.join(dst_folder, dst_name)
    tar = tarfile.open(name=dst_path, mode="w:%s" % compression)
    tar.add(folder_to_dir, os.path.basename(folder_to_dir))


def create_tar_file(app_name, tag, tmp_folder):
    """
    生成压缩包 吐出压缩包文件路径
    :param app_name:
    :param tag:
    :param tmp_folder:
    :return: {"status": 0, "msg": "success", "data"}
    """
    dst_name = "%s-%s.tar.gz" % (app_name, tag)
    dst_path = os.path.join(PACKAGE_PATH, dst_name)
    if os.path.exists(dst_path):  # 删除之前的包文件
        os.remove(dst_path)
    tar = tarfile.open(name=dst_path, mode="w:gz")
    tar.add(os.path.join(tmp_folder, app_name), os.path.basename(app_name))

    if os.path.isfile(dst_path):
        return {"status": 0, "msg": "success", "data": dst_path}
    else:
        return {"status": -1, "msg": "file not found: %s" % dst_path, "data": None}


def main(src_dir=None, app_name=None, tag=None, del_files=""):
    """

    :param src_dir: string
    :param app_name: string
    :param tag: string
    :param del_files: string 要删除的文件列表 中间以空格隔开
    :return: {"status": 0, "msg": "success", "data": None}
    """
    #创建临时目录
    ret = create_tmp_folder(app_name=app_name, src_dir=src_dir)
    if 0 != ret["status"]:
        if os.path.isdir(ret["data"]):
            shutil.rmtree(ret["data"])
        return {"status": ret["status"], "msg": ret["msg"], "data": None}
    tmp_folder = ret["data"]
    # 复制文件
    ret = cp_file(app_name=app_name, src_dir=src_dir, dest_dir=tmp_folder)
    if 0 != ret["status"]:
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)
        return {"status": ret["status"], "msg": ret["msg"], "data": None}
    # 删除不必要的文件
    del_file(app_name=app_name, tmp_folder=tmp_folder, filters=del_files)
    # 生成version.ini
    make_version(tag=tag, app_name=app_name, tmp_folder=tmp_folder)
    # 生成package.conf.yaml
    ret = create_yaml(app_name=app_name, tmp_folder=tmp_folder)
    if 0 != ret["status"]:
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)
        return {"status": ret["status"], "msg": ret["msg"], "data": None}
    # 打压缩包
    ret = create_tar_file(app_name=app_name, tag=tag, tmp_folder=tmp_folder)
    if 0 != ret["status"]:
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)
        return {"status": ret["status"], "msg": ret["msg"], "data": None}
    if os.path.isdir(tmp_folder):
        shutil.rmtree(tmp_folder)
    return {"status": 0, "msg": "success", "data": ret["data"]}


if __name__ == "__main__":

    src_dir = SRC_DIR
    tag = version
    #ret = main(src_dir="/tmp/easyops_test/workspace/nano_build_test", app_name="nano_build_test", tag="4.0", del_files="")
    ret = main(src_dir=src_dir, app_name=app_name, tag=tag, del_files=filters)
    PutStr("STATUS", str(ret["status"]))
    PutStr("MESSAGE", str(ret["msg"]))
    if 0 != ret["status"]:
        PutStr("TAR_PATH", str(""))
    else:
        PutStr("TAR_PATH", str(ret["data"]))
    print ret["msg"]
    print ret["data"]