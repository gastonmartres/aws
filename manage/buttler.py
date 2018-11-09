#!/usr/bin/python
#  -*- coding: utf-8 -*-
# Author: Gaston Martres <gastonmartres@gmail.com>

import boto3
import argparse
import json
import locale
import sys
import os
import time
import ConfigParser

locale.setlocale(locale.LC_ALL,'es_AR.UTF-8')

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


# Parser de parametros
parser = argparse.ArgumentParser(description='A little helper to start or stop EC2 instances defined in config file for use in a scheduled way, such as cronjobs.')
parser.add_argument('--profile',help="Set the profile to use when fetching or uploading parameters. \nIf no profile is provided, ENV variables and .aws/config is used by default.",default='default')
parser.add_argument('--debug',help="Debug mode, TODO", action="store_true",default=False)
parser.add_argument('--region',help='Sets the region from where to gather data. Defaults to us-east-1',default='us-east-1')
parser.add_argument('--config', help='Specify the config file.',type=str,required=True)
parser.add_argument('--skip-rds', help='Skip start/stop of RDS instances.', action='store_true',default=False)
parser.add_argument('--skip-ec2', help='Skip start/stop of EC2 instances.', action='store_true',default=False)
parser.add_argument('--verbose',help='Show more information.', action='store_true',default=False)
action = parser.add_mutually_exclusive_group(required=False)
action.add_argument('--start',help='Start instances.',action='store_true',default=False)
action.add_argument('--stop',help='Stop intances',action='store_true',default=False)
action.add_argument('--status',help='Shows instances status',action='store_true',default=False)

# parser.add_argument('--all',help="Apply the action to all instances in the config file",action='store_true',default=False)
args = parser.parse_args()

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

# Asignamos variables
profile = args.profile
aws_region = args.region
aws_access_key = config.get(profile,'aws_access_key')
aws_secret_key = config.get(profile,'aws_secret_key')
tag_key = config.get('general','tag_key')
values_to_skip = config.get('general','values_to_skip').split(",")
show_status = args.status
verbose = args.verbose
instances = []
rds_instances = []
instance_to_check = []

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
    time.sleep(1)

def stopRdsInstance(rdsInstanceId):
    print "Stopping %s" % (rdsInstanceId)
    time.sleep(1)

def checkInstanceStatus(instanceId,state):
    c = session.client('ec2')
    response = c.describe_instance_status(InstanceIds=instanceId,IncludeAllInstances=True)
    for i in response['InstanceStatuses']:
        instance = i['InstanceId']
        state_name = i['InstanceState']['Name']
        code = i['InstanceState']['Code']
        print "Instance: %s, State: %s (%s)" % (instance,state_name,code)
        if code == state:
            instance_to_check.remove(instance)

if __name__ == "__main__":
    print "Using profile %s" % (bold(green(args.profile)))
    global session
    session = boto3.Session(aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key,region_name=aws_region)
    
    # Seccion instancias EC2
    if not args.skip_ec2:
        # Instancias EC2
        print bold("[ Gathering information for EC2 instances ]")
        try:
            client = session.client('ec2')
            response = client.describe_instances()
            for i in range(len(response['Reservations'])):
                for z in range(len(response['Reservations'][i]['Instances'])):
                    _instance = response['Reservations'][i]['Instances'][z]['InstanceId']
                    _state = response['Reservations'][i]['Instances'][z]['State']['Name']
                    # Muestro el status de las instancias.
                    if show_status or verbose:
                        print bold(green(_instance)) + ", State: " + yellow(_state)
                    for x in response['Reservations'][i]['Instances'][z]['Tags']:
                        if x['Key'] == tag_key:
                            if x['Value'] in values_to_skip:
                                continue
                            
                            if x['Value'] == 'office':
                                if args.stop:
                                    if _state == 'running':
                                        instances.append(_instance)
                                if args.start:
                                    if _state == 'stopped':
                                        instances.append(_instance)
        except Exception,e:
            print "[%s] - %s" % (bold(red("ERROR")),e)
            sys.exit(1)

    # Seccion para RDS
    if not args.skip_rds:
        # Instancias RDS
        print bold("[ Gathering information for RDS Instances ]")
        try:
            client = session.client("rds")
            response = client.describe_db_instances()
            for i in range(len(response['DBInstances'])):
                _db_instance = response['DBInstances'][i]['DBInstanceIdentifier']
                _db_resource_id = response['DBInstances'][i]['DbiResourceId']
                _db_status = response['DBInstances'][i]['DBInstanceStatus']
                _db_instance_arn = response['DBInstances'][i]['DBInstanceArn']
                
                if show_status or verbose:
                    print _db_instance + " : " + _db_resource_id + " : " + _db_status
                
                # Como AWS no pone los tags en describe_db_instance, hay que hacer una segunda llamada con el ARN de la DB.
                tags = client.list_tags_for_resource(ResourceName=_db_instance_arn)
                for x in tags['TagList']:
                    if x['Key'] == tag_key:
                        
                        if x['Value'] in values_to_skip:
                            continue
                        
                        if x['Value'] == 'office':
                            if args.stop:
                                if _db_status == 'available':
                                    rds_instances.append(_db_instance)
                            if args.start:
                                if _db_status == 'stopped':
                                    rds_instances.append(_db_instance)
                    # print "%s : %s" % (x['Key'],x['Value'])
        except Exception,e:
            print "[%s] - %s" % (bold(red("ERROR")),e)
            sys.exit(1)

    # Acciones
    if args.stop:
        if not args.skip_ec2:
            print bold("[ Stopping EC2 instances ]")
            if len(instances) < 1:
                print("[%s] - There were no EC2 instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_key)))
            else:
                for i in instances:
                    if stopInstance(i):
                        print "Command sent succesfuly"
                    else:
                        print "Something went wrong..."
        if not args.skip_rds:
            print bold("[ Stopping RDS instances ]")
            if len(rds_instances) < 1:
                print("[%s] - There were no RDS instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_key)))
            else:
                for i in rds_instances:
                    stopRdsInstance(i)

    if args.start:
        if not args.skip_ec2:
            print bold("[ Starting EC2 instances ]")
            if len(instances) < 1:
                print("[%s] - There were no EC2 instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_key)))
            else:
                for i in instances:
                    if startInstance(i):
                        print "Command sent succesfuly"
                    else:
                        print "Something went wrong..."
        if not args.skip_rds:
            print bold("[ Starting RDS instances ]")
            if len(rds_instances) < 1:
                print("[%s] - There were no RDS instances with the tag %s available. None will be started/stopped." % (bold(red("WARNING")),yellow(tag_key)))
            else:
                for i in rds_instances:
                    startRdsInstance(i)
           
    if len(instance_to_check) > 0:
        if args.stop:
            state = 80
            state_name = 'stopped'
        if args.start:
            state = 16
            state_name = 'running'
        while True:
            if len(instance_to_check) == 0:
                print "[%s] - All instances %s" % (bold(yellow("INFO")),state_name)
                sys.exit(0)
            else: 
                print "[%s] - Instances left: %i" % (bold(yellow("INFO")),len(instance_to_check))
                checkInstanceStatus(instance_to_check,state)
                time.sleep(10)