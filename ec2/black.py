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

action = parser.add_mutually_exclusive_group(required=False)
action.add_argument('--start',help='Start instances.',action='store_true',default=False)
action.add_argument('--stop',help='Stop intances',action='store_true',default=False)
action.add_argument('--status',help='Shows instances status',action='store_true',default=False)

parser.add_argument('--all',help="Apply the action to all instances in the config file",action='store_true',default=False)
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

if __name__ == "__main__":
    
    #Creamos el pointer a la conexion de AWS
    if args.profile ==  None:
        try:
            client = boto3.client('ec2',region_name=args.region)
            print "\n---=[ Connecting to AWS without a profile... ]=---"
        except Exception, e:
            print "[No Profile] - Error setting client connection: %s" % (red(str(e)))
            sys.exit(1)

    elif args.profile == 'default':
        try:
            with_profile = False
            ec2_instances = config.get(args.profile,'ec2_instances').split(',')
            rds_instances = config.get(args.profile,'rds_instances').split(',')
            print "\n---=[ Connecting to AWS without a profile... ]=---"
        except Exception, e:
            print "[No Profile] - Error setting client connection: %s" % (red(str(e)))
            sys.exit(1)
    else:
        try:
            with_profile = True
            print "\n---=[ Connecting to AWS with profile %s ... ]=---" % (green(str(args.profile)))
            session = boto3.Session(profile_name=args.profile,region_name=args.region)
            ec2_instances = config.get(args.profile,'ec2_instances').split(',')
            rds_instances = config.get(args.profile,'rds_instances').split(',')
        except Exception, e:
            print "[Profile] - Error setting client connection: %s" % (red(str(e)))
            sys.exit(1)  

    if args.stop:
        print "Shutting Down EC2 instances:..."
        if with_profile:
            client = session.client('ec2')
        else:
            client = boto3.client('ec2',region_name=args.region)
        for i in ec2_instances:
            print "Shutting down %s" % (red(i))
            try:
                response = client.stop_instances(InstanceIds=[i])
                while True:
                    status = client.describe_instances(InstanceIds=[i])
                    for x in status['Reservations']:
                        for z in x['Instances']:
                            code = z['State']['Code']
                            name = z['State']['Name']                            
                    if code == 80:
                        print "Instance %s stopped." % (green(i))
                        break
                    else:
                        print yellow(name)
                        time.sleep(15)
            except Exception,e:
                print "Error: %s" % (red(bold(e)))
        print "Shutting Down RDS instances:..."
        if with_profile:
            client = session.client('rds')
        else:
            client = boto3.client('rds',region_name=args.region)
        for i in rds_instances:
            print "Shutting down %s" % (red(i))
            try:
                response = client.stop_db_instance(
                    DBInstanceIdentifier=i
                )
                print response
            except Exception, e:
                print "RDS Instance %s already down." % (i)

    if args.start:
        if with_profile:
            client = session.client('ec2')
        else:
            client = boto3.client('ec2',region_name=args.region)
        for i in ec2_instances:
            print "Starting %s" % (green(i))
            response = client.start_instances(InstanceIds=[i])
            while True:
                status = client.describe_instances(InstanceIds=[i])
                for x in status['Reservations']:
                    for z in x['Instances']:
                        code = z['State']['Code']
                        name = z['State']['Name']                            
                if code == 16:
                    print "Instance %s started." % (green(i))
                    break
                else:
                    print yellow(name)
                    time.sleep(15)
        if with_profile:
            client = session.client('rds')
        else:
            client = boto3.client('rds',region_name=args.region)
        for i in rds_instances:
            print "Shutting down %s" % (red(i))
            try:
                response = client.start_db_instance(
                    DBInstanceIdentifier=i
                )
                print response
            except Exception, e:
                print "RDS Instance %s already up." % (i)
                
    if args.status:
        if args.all:
            print bold("[EC2 Instances status]")
            if with_profile:
                client = session.client('ec2')
            else:
                client = boto3.client('ec2',region_name=args.region)
            status = client.describe_instances()
            for x in status['Reservations']:
                for z in x['Instances']:
                    state = z['State']['Name']
                    instance = z['InstanceId']
                    for i in z['Tags']:
                        if i['Key'] == 'Name':
                            name = i['Value']
                    if state in ('shutting-down'):
                        c_state = yellow(state)
                    if state in ('stopped','stopping'):
                        c_state = bold(red(state))
                    if state in ('running'):
                        c_state = green(state)
                    if state in ('terminated'):
                        c_state = bold(purple(state))

                    print "Instance %s (%s) in state %s" % (bold(green(name)),yellow(instance),c_state)
            print bold("[RDS Instances status]")
            if with_profile:
                client = session.client('rds')
            else:
                client = boto3.client('rds',region_name=args.region)
            status = client.describe_db_instances()
            for x in status['DBInstances']:
                if x['DBInstanceStatus'] in ('available'):
                    state = green(x['DBInstanceStatus'])
                elif x['DBInstanceStatus'] in ('stopped','stopping'):
                    state = bold(red(x['DBInstanceStatus']))
                print "RDS Instance %s in state %s" % (green(x['DBInstanceIdentifier']),state)
        else:
            print bold("[EC2 Instances status]")
            if with_profile:
                client = session.client('ec2')
            else:
                client = boto3.client('ec2',region_name=args.region)
            status = client.describe_instances(InstanceIds=ec2_instances)
            for x in status['Reservations']:
                for z in x['Instances']:
                    state = z['State']['Name']
                    instance = z['InstanceId']
                    for i in z['Tags']:
                        if i['Key'] == 'Name':
                            name = i['Value']
                    if state in ('shutting-down'):
                        c_state = yellow(state)
                    if state in ('stopped','stopping'):
                        c_state = bold(red(state))
                    if state in ('running'):
                        c_state = green(state)
                    if state in ('terminated'):
                        c_state = bold(purple(state))
                    print "Instance %s (%s) in state %s" % (bold(green(name)),yellow(instance),c_state)
            print bold("[RDS Instances status]")
            if with_profile:
                client = session.client('rds')
            else:
                client = boto3.client('rds',region_name=args.region)
            for i in rds_instances:
                status = client.describe_db_instances(DBInstanceIdentifier=i)
                for x in status['DBInstances']:
                    if x['DBInstanceStatus'] in ('available'):
                        state = green(x['DBInstanceStatus'])
                    elif x['DBInstanceStatus'] in ('stopped','stopping'):
                        state = bold(red(x['DBInstanceStatus']))
                    print "RDS Instance %s in state %s" % (green(x['DBInstanceIdentifier']),state)
