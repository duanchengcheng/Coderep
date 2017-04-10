#!/usr/local/easyops/python/bin/python
# -*- coding: utf-8 -*-
import sys
import time
import base64
import requests
import traceback
import logging

FORMAT = '[line %(lineno)d-%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

ORG = 8888
CMDB_HOST = '192.168.100.162'
DEPLOY_HOST = '192.168.100.162'
cmdb_header = 'cmdb.easyops-only.com'
deploy_header = 'deploy.easyops-only.com'

headers = {
    'org': ORG,
    'user': 'defaultUser',
    'Host': '',
}


def maintain(kwargs):
    params = {
        'operator':     kwargs['operator'],
        'appId':        kwargs['appId'],
        'clusterType':  kwargs['clusterType'],
        'packageId':    kwargs['packageId'],
        'ipList':       kwargs['ipList'],
        'installPath':  kwargs['installPath'],
        'opType':       kwargs['opType'],
        'platform':     kwargs['platform'],
    }
    url = 'http://%s/operation/maintain' % DEPLOY_HOST
    headers['Host'] = deploy_header
    resp = requests.post(url, data=params, headers=headers)

    return resp.status_code, resp.json()


def install(kwargs):
    url = 'http://%s/operation/install' % DEPLOY_HOST
    headers['Host'] = deploy_header
    params = {
        'operator':     kwargs['operator'],
        'appId':        kwargs['appId'],
        'packageId':    kwargs['packageId'],
        'clusterId':    kwargs['clusterId'],
        'clusterType':  kwargs['clusterType'],
        'ipList':       kwargs['ipList'],
        'installPath':  kwargs['installPath'],
        'versionId':    kwargs['versionId'],
        'versionName':  kwargs['versionName'],
        'type':         kwargs['type'],
        'autoStart':            'true' if kwargs['type'] == '1' else 'false',
        'simulateInstall':      'false',
        'platform':     kwargs['platform'],
    }

    if SIMULATEINSTALL:
        params['autoStart'] = 'false'
        params['simulateInstall'] = 'true'

    resp = requests.post(url, data=params, headers=headers)

    return resp.status_code, resp.json()


def update(kwargs):
    url = 'http://%s/operation/update' % DEPLOY_HOST
    headers['Host'] = deploy_header
    params = {
        'operator':         kwargs['operator'],
        'appId':            kwargs['appId'],
        'ipList':           kwargs['ipList'],
        'installPath':      kwargs['installPath'],
        'packageId':        kwargs['packageId'],
        'versionIdFrom':    kwargs['versionIdFrom'],
        'versionIdTo':      kwargs['versionIdTo'],
        'versionNameFrom':  kwargs['versionNameFrom'],
        'versionNameTo':    kwargs['versionNameTo'],
        'postRestart':      'true' if kwargs['type'] == '1' else 'false',
        'preStop':          'true' if kwargs['type'] == '1' else 'false',
        'forceUpdate':      'true',
        'type':             kwargs['type'],
        'clusterId':        kwargs['clusterId'],
        'clusterType':      kwargs['clusterType'],
        'platform':         kwargs['platform'],
    }

    if cluster_name == u'FOSS生产环境' and cluster_type == '2':
        params['preStop'] = 'false'
        params['postRestart'] = 'false'
        params['forceUpdate'] = 'false'

    if kwargs['versionIdTo'] == kwargs['versionIdFrom']:
        return 302, 'no need to update with the same version %s' % kwargs['versionNameFrom']

    resp = requests.post(url, data=params, headers=headers)

    return resp.status_code, resp.json()


OPERATION = {
    'install':      install,
    'update':       update,
    'restart':      maintain,
    'start':        maintain,
    'stop':         maintain,
    'uninstall':    maintain,
}


def get_apps(business_name, app_names):
    url = 'http://%s/object/instance/list/APP' % CMDB_HOST
    params = {
        'page': 1,
        'pageSize': 200,
    }
    if business_name:
        params['businesses:name$eq'] = base64.b64encode(business_name.encode('utf-8'))
    if app_names:
        params['name$in'] = ','.join([ base64.b64encode(app.encode('utf-8')) for app in app_names ])
    headers['Host'] = cmdb_header

    resp = requests.get(url, params=params, headers=headers)

    apps = []
    recs = resp.json()['data'].get('list', [])

    for rec in recs:
        apps.append({
            'name': rec['name'],
            'appId': rec['appId'],
            '_packageList': rec['_packageList'] or [],
            'clusters': rec['clusters'],
        })

    return apps


def get_package(package_id):
    url = 'http://%s/package/%s' % (DEPLOY_HOST, package_id)
    headers['Host'] = deploy_header

    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        return resp.json()['data']

    return {}


def get_package_version(package_id, version_name):
    url = 'http://%s/version/list' % DEPLOY_HOST
    params = { 'packageId': package_id, 'page': 1, 'pageSize': 200, 'order': 'ctime desc' }
    headers['Host'] = deploy_header
    res = {}

    try:
        resp = requests.get(url, params=params, headers=headers)
        versions = resp.json()['data']['list']
        for version in versions:
            if not version_name:
                res = version
                break

            if version['name'] == version_name:
                res = version
                break
    except:
        logger.error(traceback.format_exc())
        res = {}

    return res


def get_instance_version(package_id, device_id, device_ip):
    url = 'http://%s/instance/search' % DEPLOY_HOST
    headers['Host'] = deploy_header
    params = {
        'packageId': package_id,
        'deviceId': device_id,
        'deviceIp': device_ip,
        'page': 1,
        'pageSize': 1
    }

    try:
        resp = requests.get(url, params=params, headers=headers)
        result = resp.json()['data']['list']
        if not result:
            return -1, {}

        if not len(result) == 1:
            return 1, {}

        return 0, result[0]

    except:
        logger.error(traceback.format_exc())
        return 2, {}


def get_task_summary(task_id):
    url = 'http://%s/operation/summary/%s' % (DEPLOY_HOST, task_id)
    headers['Host'] = deploy_header

    resp = requests.get(url, headers=headers)

    return resp.status_code, resp.json()


def get_task_subtask(task_id):
    url = 'http://%s/operation/subtask/%s' % (DEPLOY_HOST, task_id)
    headers['Host'] = deploy_header

    resp = requests.get(url, headers=headers)

    return resp.status_code, resp.json()


def query_operation_reuslt(apps, result, business_name, operation, cluster_name, cluster_type):
    total_try = 180
    logger.info(u'requesting %s result -------------------' % operation)

    while total_try:
        all_finished = True
        for package_name, info in result.iteritems():
            if not info['taskId']:
                continue

            app_name = info['app_name']
            code, msg = get_task_summary(info['taskId'])
            if code == 200:
                if msg['data']['status'] == 'wait':
                    all_finished = False
                    logger.info(u'%s %s %s, waiting ...' % (app_name, operation, package_name))
                elif msg['data']['status'] == 'run':
                    all_finished = False
                    logger.info(u'%s %s %s, running ...' % (app_name, operation, package_name))
                else:
                    info['status'] = msg['data']['status']
            else:
                logger.error(u'request summary error: %s %s' % (code, msg))
                all_finished = False

        if all_finished:
            break

        total_try -= 1
        time.sleep(3)

    total = 0
    fail = 0
    success = 0
    logger.info(u'statistics ---------------')
    for name, info in result.iteritems():
        total += 1
        if not info['taskId']:
            logger.warn(u'%s %s' % (name, info['msg']))
            fail += 1
            continue

        if info['status'] == 'ok':
            success += 1
            continue

        fail += 1
        logger.info(u'%s - summary status: %s' % (name, info['status']))
        code, msg = get_task_subtask(info['taskId'])
        if code == 200:
            for e in msg['data']:
                logger.info(u'%s %s %s' % (e['ip'], e['status'], e['detail']))
        else:
            logger.warn(u'request subtask error: %s %s' % (code, msg))

    logger.info(u'total %s, success %s, fail %s' % (total, success, fail))


def build_params(operation, app, cluster, package):
    res = {}

    res['operator'] = headers['user']
    res['appId'] = app['appId']
    res['opType'] = operation
    res['clusterType'] = cluster['type']
    res['clusterId'] = cluster['clusterId']
    res['ipList'] = cluster['ipList']
    res['type'] = package['type']
    res['packageId'] = package['packageId']
    res['installPath'] = package['installPath']
    res['versionName'] = package['version']
    res['platform'] = package['platform']

    if operation in ['install', 'update']:
        app_package = get_package_version(package['packageId'], package['version'])
        if app_package:
            res['versionName'] = app_package['name']
            res['versionId'] = app_package['versionId']
        else:
            msg = 'no such an package version %s, please check and try again later' % package['version']
            return msg, {}

        if operation == 'update':
            device = cluster['deviceList'][0]

            code, current_version = get_instance_version(package['packageId'],
                                                         device['deviceId'], device['ip'])
            if code == -1:
                msg = 'have not installed any version yet, please install first'
                return msg, {}
            if code:
                msg = 'error found, code %s' % code
                return msg, {}

            res['versionIdFrom'] = current_version['versionId']
            res['versionNameFrom'] = current_version['versionName']
            res['versionIdTo'] = res['versionId']
            res['versionNameTo'] = res['versionName']

    return '', res


def main(business_name, operation, cluster_name, cluster_type,
         app_names=None, package_names=None, config_names=None,
         package_version=None, config_version=None):
    apps = get_apps(business_name, app_names)

    result = {}
    for app in apps:
        if app['name'] in exclude_app_names:
            continue

        clusters = app.get('clusters') or []
        cluster = {}

        for c in clusters:
            if c['name'] == cluster_name and c['type'] == cluster_type:
                cluster['clusterId'] = c['clusterId']
                cluster['_packageList'] = c.get('_packageList', [])
                cluster['deviceList'] = c['deviceList']
                device_list = c.get('deviceList') or []
                cluster['ipList'] = ';'.join([ d['ip'] for d in device_list ])
                cluster['name'] = cluster_name
                cluster['type'] = cluster_type
                break

        if not cluster:
            logger.warn(u'%s -- no such a cluster named %s, with type %s' % (app['name'], cluster_name, cluster_type))
            continue

        if not cluster['deviceList']:
            logger.warn(u'%s -- no device in cluster -- %s' % (app['name'], cluster_name))
            continue

        # the order matters, config package should be first to install or update
        package_ids = []
        # TODO: can NOT uninstall config package alone.
        if operation in ['install', 'update']:
            for package in cluster['_packageList']:
                package_ids.append(package['packageId'])

        for package in app['_packageList']:
            if not package.get('installPath'):
                logger.warn('%s, package wrong' % app['name'])
                continue

            if package['installPath'].endswith('jdk') or package['installPath'].endswith('jboss-eap'):
                continue
            package_ids.append(package['packageId'])

        if not package_ids:
            logger.warn(u'%s -- 还没绑定任何应用包或配置包，请先绑定' % app['name'])
            continue

        for package_id in package_ids:
            try:
                package = get_package(package_id)
                if not package:
                    continue

                # if not package['name'] == app['name']:
                #     continue

                info = ''
                if package['type'] == '1':
                    if package_names and package['name'] not in package_names:
                        continue
                    info = u'应用包-`%s`' % package['name']
                    package['version'] = package_version
                elif package['type'] == '2':
                    if config_names and package['name'] not in config_names:
                        continue
                    info = u'配置包-`%s`' % package['name']
                    package['version'] = config_version

                logger.info(u'%s: %s' % (app['name'], info))
                msg, kwargs = build_params(operation, app, cluster, package)
                if msg:
                    result[package['name']] = {'taskId': '', 'msg': msg, 'app_name': app['name']}
                    continue

                if operation == 'install':
                    logger.info(u'install %s with version %s' % (info, kwargs['versionName']))
                elif operation == 'update':
                    logger.info(u'update package %s -> %s' % (kwargs['versionNameFrom'], kwargs['versionNameTo']))

                code, msg = OPERATION[operation](kwargs)
                if code == 200:
                    task_id = msg['data']['taskId']
                    result[package['name']] = { 'taskId': task_id, 'status': 'wait', 'app_name': app['name'] }
                else:
                    result[package['name']] = { 'taskId': '', 'msg': msg, 'app_name': app['name'] }

            except:
                logger.error(traceback.format_exc())

    query_operation_reuslt(apps, result, business_name, operation, cluster_name, cluster_type)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='operation on batch apps')
    parser.add_argument('operation', choices=OPERATION.keys(), help='operation type')
    parser.add_argument('cluster_name', help='the cluster in app to operate')
    parser.add_argument('cluster_type', choices=['0', '1', '2'], help='cluster type, 0 develop, 1 test, 2 production')
    parser.add_argument('-b', '--business_name', help='the business to operate')
    parser.add_argument('-o', '--org', help='the org, default %s' % ORG)
    parser.add_argument('-c', '--cmdb_host', help='the cmdb host, default %s' % CMDB_HOST)
    parser.add_argument('-d', '--deploy_host', help='the deploy host, default %s' % DEPLOY_HOST)
    parser.add_argument('-an', '--app_names', help='the app names to operate, default all apps')
    parser.add_argument('-pn', '--package_names', help='the package names to install/update, default all packages')
    parser.add_argument('-cn', '--config_names', help='the config names to install/update, default all config packages')
    parser.add_argument('-av', '--package_version', help='the app version to operate, default the latest version')
    parser.add_argument('-cv', '--config_version', help='the cluster version to operate, default the latest version')
    parser.add_argument('--exclude_app_names', help='the app names to operate, default all apps')
    parser.add_argument('--simulate_install', action='store_true', help='set simulate install, used only with install operation')
    args = parser.parse_args()

    if args.org:
        headers['org'] = args.org

    if args.cmdb_host:
        CMDB_HOST = args.cmdb_host

    if args.deploy_host:
        DEPLOY_HOST = args.deploy_host

    cluster_name = args.cluster_name.decode('utf-8')
    cluster_type = args.cluster_type
    business_name = ''
    if args.business_name:
        business_name = args.business_name.decode('utf-8')
    app_names = []
    if args.app_names:
        app_names = args.app_names.split(',')
        app_names = list(set(app_names))
        app_names = [ app.decode('utf-8') for app in app_names ]

    exclude_app_names = []
    if args.exclude_app_names:
        exclude_app_names = args.exclude_app_names.split(',')
        exclude_app_names = list(set(exclude_app_names))
        exclude_app_names = [ app.decode('utf-8') for app in exclude_app_names ]

    SIMULATEINSTALL = False
    if args.simulate_install:
        SIMULATEINSTALL = True

    package_names = []
    if args.package_names:
        package_names = args.package_names.split(',')
        package_names = list(set(package_names))
        package_names = [ package.decode('utf-8') for package in package_names ]

    config_names = []
    if args.config_names:
        config_names = args.config_names.split(',')
        config_names = list(set(config_names))
        config_names = [ config.decode('utf-8') for config in config_names ]

    main(business_name, args.operation, cluster_name, cluster_type,
         app_names=app_names, package_names=package_names, config_names=config_names,
         package_version=args.package_version, config_version=args.config_version)

