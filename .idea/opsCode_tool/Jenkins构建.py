#!/usr/local/easyops/python/bin/python
# encoding: utf-8

"""
给Jenkins server发送构建请求，并将构建结果返回

input parameters:

git_tag_name: git_tag用于构建和生成版本号
jenkins_job_url: Jenkins构建项目URL
username: 用户名
password: 密码

output parameters:

WORKSPACE: jenkins构建的项目空间
REMOTE_HOST: Jenkins构建项目文件存储IP
"""

import re
import jenkins
import logging
from time import sleep

FORMAT = "[line %(lineno)d-%(levelname)s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("log")
logger.setLevel(logging.DEBUG)


def build_project(jenkins_server_url, username=None, password=None, job_name=None, git_tag_name=None, timeout=1800):
    # 构建项目

    if username:
        server = jenkins.Jenkins(jenkins_server_url, username, password)
        # print server.get_whoami()
    else:
        server = jenkins.Jenkins(jenkins_server_url)

    try:
        next_build_number = server.get_job_info(job_name)['nextBuildNumber']

        if git_tag_name:
            server.build_job(job_name, parameters={'INPUT_TAG_NAME': git_tag_name})
        else:
            print "没有输入版本号，将不使用版本匹配"
            server.build_job(job_name)
    except Exception, e:
        if "authentication failed" in e:
            print "认证失败！"
        print e
        exit(4)

    # 等待 jenkins 有个pending的过程
    sleep(10)

    # 获取构建信息
    logger.info("%s, %s" % (job_name, next_build_number))
    build_info = server.get_build_info(job_name, next_build_number)

    if timeout:
        timeout = timeout
    else:
        timeout = 1800
    time_used = 0
    while build_info["building"] and time_used < timeout:
        time_used += 5
        sleep(5)
        build_info = server.get_build_info(job_name, next_build_number)
    status = build_info['result']
    remote_host = build_info["builtOn"]
    # 获取控制台信息
    if status == 'SUCCESS':
        console_msg = server.get_build_console_output(job_name, next_build_number)
        m = re.search(r" in workspace (.+)", console_msg)
        if m:
            project_path = m.group(1)
            logger.info(u"构建成功，包workspack路径: %s" % project_path)
        else:
            logger.warn(u'未获取到构建后的路径信息，请检查Jenkins控制台输出.')
            exit(5)
    else:
        logger.error(u"构建失败，请检查Jenkins控制台输出.")
        exit(6)

    return status, project_path, remote_host

if __name__ == '__main__':
    if 'job' in jenkins_job_url:
        jenkins_server_url = jenkins_job_url.split('job')[0]
        job_name = jenkins_job_url.split('job')[1].split('/')[1]
        if not jenkins_server_url:
            print u"没有获取到Jenkins服务URL，请检查输入是否正确！"
            exit(1)
        if not job_name:
            print u"没有获取到Jenkins的项目名称，请检查输入是否正确！"
            exit(2)
    else:
        logger.warn(u'jenkins_job_url 不符合格式要求')
        exit(3)

    if not username:
        print "没有输入用户名，将不使用认证"
        if password:
            print "您输入了密码，将被忽略！"
            password = ""
    else:
        if not password:
            print "没有输入密码！"
            exit(4)


    logger.info(u'Jenkins构建项目名称: %s' % job_name)
    task_status, task_path, remote_host = build_project(jenkins_server_url, username, password, job_name=job_name, git_tag_name=git_tag_name)
    PutStr("JOB_NAME", job_name)
    PutStr("WORKSPACE", task_path)
    PutStr("REMOTE_HOST", remote_host)