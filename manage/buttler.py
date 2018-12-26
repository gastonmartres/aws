#!/usr/bin/python
#  -*- coding: utf-8 -*-
# Author: Gaston Martres <gastonmartres@gmail.com>
#
# TODO: 
# - Chequeo de horario
# - Lectura de tags correspondiente a como se ejecuta el ambiente (onDemand, officehours, onLine)

import boto3
import argparse
import json
import locale
import sys
import os
import time
import ConfigParser
import textwrap

locale.setlocale(locale.LC_ALL,'es_AR.UTF-8')

# Parser de parametros
parser = argparse.ArgumentParser(description='A little helper to start or stop EC2 instances defined in config file for use in a scheduled way, such as cronjobs.')
parser.add_argument('--profile',help="Set the profile to use when fetching or uploading parameters.",required=True)
parser.add_argument('--debug',help="Debug mode, TODO", action="store_true",default=False)
parser.add_argument('--region',help='Sets the region from where to gather data. Defaults to us-east-1',default='us-east-1')
parser.add_argument('--config', help='Specify the config file.',type=str,required=True)
parser.add_argument('--skip-rds', help='Skip start/stop of RDS instances.', action='store_true',default=False)
parser.add_argument('--skip-ec2', help='Skip start/stop of EC2 instances.', action='store_true',default=False)
parser.add_argument('--verbose',help='Show more information.', action='store_true',default=False)
parser.add_argument('--env', help='Target environment, ex: qa, dev, uat. The tag must exists.',type=str,default="None")
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument('--start',help='Start instances.',action='store_true',default=False)
action.add_argument('--stop',help='Stop intances',action='store_true',default=False)
action.add_argument('--status',help='Shows instances status',action='store_true',default=False)
action.add_argument('--reserve',help='Reserve the specified environment.',action='store_true',default=False)
action.add_argument('--free',help='Free the specified environment',action='store_true',default=False)

args = parser.parse_args()

#---[ Colores ]-----------------------------------------------------------------
def black(string):
    HEADER = '\033[30m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def red(string):
    HEADER = '\033[31m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def green(string):
    HEADER = '\033[32m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def yellow(string):
    HEADER = '\033[33m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def blue(string):
    HEADER = '\033[34m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def purple(string):
    HEADER = '\033[35m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def cyan(string):
    HEADER = '\033[36m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def white(string):
    HEADER = '\033[37m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def grey(string):
    HEADER = '\033[38m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

def bold(string):
    HEADER = '\033[1m'
    ENDC = '\033[0m'
    return HEADER + str(string) + ENDC

# ---[ Chequeos]---
# Archivo de configuracion
if os.path.exists(args.config):
    if os.path.isfile(args.config):
        config = ConfigParser.ConfigParser()
        config.read(args.config)
    else:
        print "%s is not a configuration file." % (args.config)
        sys.exit(False)
else:
    print "Configuration file missing, please create one."
    sys.exit(False)


def stopInstance(instanceId):
    print "Stopping %s" % (instanceId)
    try:
        c = session.client('ec2')
        response = c.stop_instances(InstanceIds=[instanceId])
        if response['StoppingInstances'][0]['CurrentState']['Code'] != '16':
            instance_to_check.append(instanceId)
            return True
        else:
            return False
    except Exception,e:
        print("[%s] - %s" % (bold(red("ERROR")),e))
    time.sleep(1)

def startInstance(instanceId):
    print "Starting %s" % (instanceId)
    try:
        c = session.client('ec2')
        response = c.start_instances(InstanceIds=[instanceId])
        if response['StartingInstances'][0]['CurrentState']['Code'] != '80':
            instance_to_check.append(instanceId)
            return True
        else:
            return False
    except Exception,e:
        print("[%s] - %s" % (bold(red("ERROR")),e))
    time.sleep(1)

def startRdsInstance(rdsInstanceId):
    print "Starting %s" % (rdsInstanceId)
    c = session.client('rds')
    response = c.start_db_instance(DBInstanceIdentifier=rdsInstanceId)
    if response['DBInstance']['DBInstanceStatus'] != "available":
        rds_instance_to_check.append(rdsInstanceId)
        return True
    else: 
        return False
    time.sleep(1)

def stopRdsInstance(rdsInstanceId):
    print "Stopping %s" % (rdsInstanceId)
    c = session.client('rds')
    response = c.stop_db_instance(DBInstanceIdentifier=rdsInstanceId)
    if response['DBInstance']['DBInstanceStatus'] != "stopped":
        rds_instance_to_check.append(rdsInstanceId)
        return True
    else: 
        return False
    time.sleep(1)

def checkInstanceStatus(instanceId,state):
    c = session.client('ec2')
    response = c.describe_instance_status(InstanceIds=instanceId,IncludeAllInstances=True)
    for i in response['InstanceStatuses']:
        instance = i['InstanceId']
        state_name = i['InstanceState']['Name']
        code = i['InstanceState']['Code']
        if debug:
            print "[DEBUG] - %s: %s" % (_db_instance,_db_status)
        fmt = "{i:s}\t{s:s}"
        print fmt.format(i=instance,s=state_name)
        if code == state:
            instance_to_check.remove(instance)
        if code == 48:
            print "Ops: Instance Terminated. Autoscaling perhaps?"
            instance_to_check.remove(instance)

def checkRdsInstanceStatus(rdsInstanceId,state):
    c = session.client('rds')
    response = c.describe_db_instances(DBInstanceIdentifier=rdsInstanceId)
    for i in range(len(response['DBInstances'])):
        db_instance = response['DBInstances'][i]['DBInstanceIdentifier']
        db_status = response['DBInstances'][i]['DBInstanceStatus']
        fmt = "{i:s}\t{s:s}"
        print fmt.format(i=db_instance,s=db_status)
        if db_status == state:
            try: 
                rds_instance_to_check.remove(db_instance)
            except Exception,e:
                print "Ups: %s" % (e)

def updateInstanceTag(instanceId,Tag,Value):
    c = session.client('ec2')
    response = c.create_tags(Resources=[instanceId],Tags=[{'Key':Tag,'Value':Value},],)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False

def updateRdsInstanceTag(rdsInstanceId,Tag,Value):
    c = session.client('rds')
    response = c.add_tags_to_resource(ResourceName=rdsInstanceId,Tags=[{'Key':Tag,'Value':Value},],)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False

if __name__ == "__main__":
    # Asignamos variables
    profile = args.profile
    aws_region = args.region
    aws_access_key = config.get(profile,'aws_access_key')
    aws_secret_key = config.get(profile,'aws_secret_key')
    tag_runmode_key = config.get('general','tag_runmode_key')
    tag_runmode_value = config.get('general','tag_runmode_value')
    values_to_skip = config.get('general','values_to_skip').split(",")
    show_status = args.status
    verbose = args.verbose
    instances = []
    rds_instances = []
    instance_to_check = []
    rds_instance_to_check = []
    debug = args.debug
    check_interval = float(config.get('general','check_interval'))
    args.env = args.env.lower().strip()

    print "Using profile %s" % (bold(green(args.profile)))
    global session
    session = boto3.Session(aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key,region_name=aws_region)
    
    # Seccion instancias EC2
    if not args.skip_ec2:
        # Instancias EC2
        print bold("[ Gathering information for EC2 instances ]")
        try:
            client = session.client('ec2')
            if args.env != "None":
                response_i = client.describe_instances(Filters=[{"Name":"tag:Env","Values":[args.env]}])
            else: 
                response_i = client.describe_instances()
            if show_status or verbose:
                print "%s\t\t%s" % (bold("InstanceID"),bold("Status"))
            for i in range(len(response_i['Reservations'])):
                for z in range(len(response_i['Reservations'][i]['Instances'])):
                    _instance = response_i['Reservations'][i]['Instances'][z]['InstanceId']
                    _state = response_i['Reservations'][i]['Instances'][z]['State']['Name']
                    # Muestro el status de las instancias.
                    if show_status or verbose:
                        fmt = "{i:s}\t{s:s}"
                        print fmt.format(i=_instance,s=_state)
                    for x in response_i['Reservations'][i]['Instances'][z]['Tags']:
                        if x['Key'] == tag_runmode_key:
                            if x['Value'] in values_to_skip:
                                continue
                            
                            if x['Value'] == tag_runmode_value:
                                if args.stop:
                                    if _state == 'running':
                                        instances.append(_instance)
                                if args.start:
                                    if _state == 'stopped':
                                        instances.append(_instance)
        except Exception,e:
            print "[%s] - %s (EC2)" % (bold(red("ERROR")),e)
            sys.exit(1)

    # Seccion para RDS
    if not args.skip_rds:
        # Instancias RDS
        print bold("[ Gathering information for RDS Instances ]")
        try:
            client = session.client("rds")
            response_db = client.describe_db_instances()
            # print response
            if show_status or verbose:
                print "%s\t\t%s\t\t\t%s" % (bold("DBName"),bold("ResourceID"),bold("Status"))
            for i in range(len(response_db['DBInstances'])):
                _db_instance = response_db['DBInstances'][i]['DBInstanceIdentifier']
                _db_resource_id = response_db['DBInstances'][i]['DbiResourceId']
                _db_status = response_db['DBInstances'][i]['DBInstanceStatus']
                _db_instance_arn = response_db['DBInstances'][i]['DBInstanceArn']
                
                # Como AWS no pone los tags en describe_db_instance, hay que hacer una segunda llamada con el ARN de la DB.
                tags = client.list_tags_for_resource(ResourceName=_db_instance_arn)
                
                if args.env != "None":
                    _db_env = []
                    _is_env = False
                    for x in tags['TagList']:
                        if x['Key'] == 'Env' and x['Value'] == args.env:
                            _db_env.append(_db_instance_arn)
                            _is_env = True
                            continue
                        if _is_env:    
                            for x in tags['TagList']:
                                if x['Key'] == tag_runmode_key:
                                    if x['Value'] in values_to_skip:
                                        continue
                                    if x['Value'] == tag_runmode_value:
                                        if show_status or verbose:
                                            fmt = "{db:s}\t{i:s}\t{s:s}"
                                            print fmt.format(db=_db_instance,i=_db_resource_id,s=_db_status)
                                        if args.stop:
                                            if _db_status == 'available':
                                                rds_instances.append(_db_instance)
                                        if args.start:
                                            if _db_status == 'stopped':
                                                rds_instances.append(_db_instance)    
                else:
                    for x in tags['TagList']:
                        if x['Key'] == tag_runmode_key:
                            if x['Value'] in values_to_skip:
                                continue
                            if x['Value'] == tag_runmode_value:
                                if show_status or verbose:
                                    fmt = "{db:s}\t{i:s}\t{s:s}"
                                    print fmt.format(db=_db_instance,i=_db_resource_id,s=_db_status)
                                if args.stop:
                                    if _db_status == 'available':
                                        rds_instances.append(_db_instance)
                                if args.start:
                                    if _db_status == 'stopped':
                                        rds_instances.append(_db_instance)    
        except Exception,e:
            print "[%s] - %s" % (bold(red("ERROR")),e)
            sys.exit(1)

    # Reserva de ambientes
    if args.reserve:
        r_error = False
        if args.skip_ec2 or args.skip_rds:
            print "ERROR, you cannot skip EC2 instances or RDS instances when you reserve an environment."
            sys.exit(0)
        if args.env == "None":
            print "ERROR, you cannot reserve ALL environments."
            sys.exit(0)
        # Instancias EC2
        for i in range(len(response_i['Reservations'])):
            for z in range(len(response_i['Reservations'][i]['Instances'])):
                _instance = response_i['Reservations'][i]['Instances'][z]['InstanceId']
                _state = response_i['Reservations'][i]['Instances'][z]['State']['Name']
                if not updateInstanceTag(_instance,'RunMode','Reserved'):
                    print "ERROR - something went wrong"
                    r_error = True
        
        # Instancias RDS
        for i in _db_env:
            if not updateRdsInstanceTag(i,'RunMode','Reserved'):
                r_error = True
        
        if r_error:
            print "ERROR - Environment %s not properly reserved." % (bold(red(args.env)))
            sys.exit(1)
        else:
            print "Environment %s properly reserved." % (bold(green(args.env)))
            sys.exit(0)
    
    # Liberacion de ambiente.
    if args.free:
        f_error = False
        if args.skip_ec2 or args.skip_rds:
            print "ERROR, you cannot skip EC2 instances or RDS instances when you free an environment."
            sys.exit(0)
        if args.env == "None":
            print "ERROR, you cannot free ALL environments."
            sys.exit(0)
        for i in range(len(response_i['Reservations'])):
            for z in range(len(response_i['Reservations'][i]['Instances'])):
                _instance = response_i['Reservations'][i]['Instances'][z]['InstanceId']
                _state = response_i['Reservations'][i]['Instances'][z]['State']['Name']
                if not updateInstanceTag(_instance,'RunMode','Office'):
                    f_error = True
        # Instancias RDS
        for i in _db_env:
            if not updateRdsInstanceTag(i,'RunMode','Office'):
                r_error = True

        if f_error:
            print "ERROR - Environment %s not properly freed." % (bold(red(args.env)))
            sys.exit(1)
        else:
            print "Environment %s properly freed." % (bold(green(args.env)))
            sys.exit(0)

    # [ Acciones ]
    # Detenemos instancias EC2 y RDS
    if args.stop:
        if not args.skip_ec2:
            print bold("[ Stopping EC2 instances ]")
            if len(instances) < 1:
                print("[%s] - There are no EC2 instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_runmode_key)))
            else:
                for i in instances:
                    if stopInstance(i):
                        print "Command sent succesfuly"
                    else:
                        print "Something went wrong..."
        if not args.skip_rds:
            print bold("[ Stopping RDS instances ]")
            if len(rds_instances) < 1:
                print("[%s] - There are no RDS instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_runmode_key)))
            else:
                for i in rds_instances:
                    stopRdsInstance(i)

    # Iniciamos instancias EC2 y RDS
    if args.start:
        if not args.skip_ec2:
            print bold("[ Starting EC2 instances ]")
            if len(instances) < 1:
                print("[%s] - There are no EC2 instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_runmode_key)))
            else:
                for i in instances:
                    if startInstance(i):
                        print "Command sent succesfuly"
                    else:
                        print "Something went wrong..."
        if not args.skip_rds:
            print bold("[ Starting RDS instances ]")
            if len(rds_instances) < 1:
                print("[%s] - There are no RDS instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_runmode_key)))
            else:
                for i in rds_instances:
                    startRdsInstance(i)
    
    # Chequeamos el estado de las instancias
    if len(instance_to_check) > 0:
        if args.stop:
            state = 80
            state_name = 'stopped'
        if args.start:
            state = 16
            state_name = 'running'
        while True:
            header = "%s\t\t%s" % (bold("Instance"),bold("Status"))
            print header
            checkInstanceStatus(instance_to_check,state)
            if len(instance_to_check) == 0:
                print "[%s] - All instances %s" % (bold(yellow("INFO")),state_name)
                break
            else:
                print "[%s] - Instances left to check: %i | Next check in %i seconds." % (bold(yellow("INFO")),len(instance_to_check),int(check_interval))
            time.sleep(check_interval)
    
    # Chequeamos el estado de las RDS
    if len(rds_instance_to_check) > 0:
        if args.stop:
            state = 'stopped'
        if args.start:
            state = 'available'
        while len(rds_instance_to_check) > 0:
            header = "%s\t%s" % (bold("RdsInstance"),bold("Status"))
            print header
            for z in rds_instance_to_check:
                checkRdsInstanceStatus(z,state)
            
            if debug:
                print "[DEBUG] - len(rds_instances_to_check): %i" % (len(rds_instance_to_check))
            if len(rds_instance_to_check) == 0:
                print "[%s] - All instances %s" % (bold(yellow("INFO")),state)
                break
            else:
                print "[%s] - RDS Instances left to check: %i | Next check in %i seconds." % (bold(yellow("INFO")),len(rds_instance_to_check),int(check_interval))
            time.sleep(check_interval)

    sys.exit(0)