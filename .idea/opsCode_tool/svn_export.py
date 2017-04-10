#!/usr/local/easyops/python/bin/python
# -*- coding: utf-8 -*-

import commands
import time
import shutil


def svn_export(svn_repo_path, svn_repo_version):

    time_now = time.time()
    package_name = "package_"+str(time_now)
    cmd = "svn export -q -r {version} --force {path} /tmp/package_{now} 2>&1".format(version=svn_repo_version,
                                                                                     path=svn_repo_path, now=time_now)
    ret = commands.getstatusoutput(cmd)
    if ret[0] != 0:
        print "execute svn command error: "+cmd
        rowInfo = "message={msg}".format(msg="execute svn command error: "+cmd)
        PutRow("SVNIntegrate", rowInfo)
        exit(1)
    tar_cmd = "cd /tmp; tar cvf {pack}.tar {pack}".format(pack=package_name)
    ret = commands.getstatusoutput(tar_cmd)
    if ret[0] != 0:
        print "execute tar command error: "+tar_cmd
        rowInfo = "message={msg}".format(msg="execute tar command error: "+cmd)
        PutRow("SVNIntegrate", rowInfo)
        exit(1)
    shutil.rmtree("/tmp/"+package_name)
    return True, "/tmp/"+package_name+".tar"


if __name__ == "__main__":
    svn_repo_path = SVN_PATH
    svn_version = VERSION
    #svn_repo_path = "svn://192.168.100.162:3690//06/32/1a/18bd1cbf87d79b5098f659b988"
    #svn_version = "r540"
    ret, tar_path = svn_export(svn_repo_path, svn_version)
    print tar_path
    if ret is True:
        rowInfo = "message={msg}".format(msg="svn export done ")
        PutRow("SVNIntegrate", rowInfo)
        PutStr("TAR_PATH", tar_path)