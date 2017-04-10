#!/usr/local/easyops/python/bin/python
# -*- coding: utf-8 -*-

import commands
import os
import shutil
import time
import traceback
import time


def git_pull(git_path, git_tag, password=""):
    project_name = git_path.split("/")[-1].split(".")[0]
    print project_name
    if os.path.exists("/tmp/"+project_name):
        print "rm ", project_name
        shutil.rmtree("/tmp/"+project_name)
    if git_path.find("http") == 0:
        expect_shell = '#!/usr/bin/expect\ncd /tmp\nspawn git clone -b master {git_path}\nexpect "Password:"\nsend ' \
                       '"{pwd}\\n"\nexpect eof\nexit'.format(git_path=git_path, pwd=password)
        try:
            file_name = "git_export_{time}".format(time=time.time())
            with open(file_name, "w") as f:
                f.write(expect_shell)
            ret = commands.getstatusoutput("expect " + file_name)
            os.remove(file_name)
            if ret[0] != 0:
                print "execute command error: "+expect_shell
                rowInfo = "message={msg}".format(msg="execute command error: "+expect_shell)
                PutRow("gitIntegrate", rowInfo)
                exit(1)
        except Exception, e:
            print traceback.format_exc()
            exit(1)
    else:
        git_pull_cmd = "cd /tmp;git clone -b master "+git_path
        ret = commands.getstatusoutput(git_pull_cmd)
        if ret[0] != 0:
            print "execute command error: "+git_pull_cmd
            rowInfo = "message={msg}".format(msg="execute command error: "+git_pull_cmd)
            PutRow("gitIntegrate", rowInfo)
            exit(1)

    tar_name = "temp_{now}.tgz".format(now=time.time())
    git_archive_tag_cmd = "cd /tmp/{project};git archive {tag} |gzip > /tmp/{tar_name}".format(project=project_name, tag=git_tag, tar_name=tar_name)
    print git_archive_tag_cmd
    ret = commands.getstatusoutput(git_archive_tag_cmd)
    print ret
    if ret[0] != 0:
        print "execute command error: "+git_archive_tag_cmd
        print ret[1]
        rowInfo = "message={msg}".format(msg="execute command error: "+git_pull_cmd+"+"+ret[1])
        #PutRow("gitIntegrate", rowInfo)
        exit(1)
    else:
        if ret[1] != "" and ret[1].find("fatal") == 0:
            print ret[1]
            rowInfo = "message={msg}".format(msg="execute command error: "+git_pull_cmd+""+ret[1])
            PutRow("gitIntegrate", rowInfo)
            exit(1)
    return True, "/tmp/"+tar_name


def assemble_git_path(git_path, username=None, password=None):
    if git_path.find("http") == 0:
        if username is None or password is None:
            print "git path is httpURL, no username or password"
            exit(1)
        else:
            strs = git_path.split("://")
            if len(strs) < 2:
                print "check git url error"
                exit(1)
            real_git_path = strs[0] + "://" + username  + "@" + strs[1]

            return real_git_path
    else:
        return git_path


if __name__ == "__main__":
    #git_path = "http://git.easyops.local/anyclouds/Deploy-P.git"
    #git_tag = "2.16.0"
    #username = "angevilzhao"
    #password = "Apollo615"
    git_path = GIT_PATH
    git_tag = GIT_TAG
    username = USERNAME if USERNAME else None
    password = PASSWORD if PASSWORD else None
    real_git_path = assemble_git_path(git_path, username, password)
    print real_git_path
    ret, tar_path = git_pull(real_git_path, git_tag, password)
    if ret:
        rowInfo = "message={msg}".format(msg="git export done")
        PutRow("gitIntegrate", rowInfo)
        PutStr("TAR_PATH", tar_path)