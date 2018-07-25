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

locale.setlocale(locale.LC_ALL,'es_AR.UTF-8')

# Parser de parametros
parser = argparse.ArgumentParser(description='A litle tool to get parameters from SSM/Parameter Store and save them into a file.')
group = parser.add_mutually_exclusive_group()
parser.add_argument('--profile',help="Set the profile to use when fetching or uploading parameters. \nIf no profile is provided, ENV variables and .aws/config is used by default.")
parser.add_argument('--path',help='Path from where to get the parameter data.')
parser.add_argument('--fileout',help="Filename of the file data will be saved.\nData will be json formatted.")
parser.add_argument('--debug',help="Debug mode, TODO", action="store_true",default=False)
parser.add_argument('--region',help='Sets the region from where to gather data. Defaults to us-east-1',default='us-east-1')

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

if __name__ == "__main__" :
    if args.path.endswith("/"):
        path = args.path
    else:
        path = args.path + "/"

    error = False

    #Creamos el pointer a la conexion de AWS
    if args.profile == None:
        try:
            client = boto3.client('ssm',region_name=args.region)
            print "\n---=[ Connecting to AWS without a profile... ]=---"
        except Exception, e:
            print "Error setting client: %s" % (red(str(e)))
            sys.exit(1)
    else:
        try:
            print "\n---=[ Connecting to AWS with profile %s ... ]=---" % (green(str(args.profile)))
            session = boto3.Session(profile_name=args.profile,region_name=args.region)
            client = session.client('ssm') 
        except Exception, e:
            print "Error setting client: %s" % (red(str(e)))
            sys.exit(1)  

    resp = client.describe_parameters(
            ParameterFilters=[
                {
                    'Key': 'Path',
                    'Option': 'Recursive',
                    'Values': [path]
                }
            ],
            MaxResults=50
            )
    
    items = []
    while resp:
        items += resp['Parameters']
        resp = client.describe_parameters(
            ParameterFilters=[
            {
                    'Key': 'Path',
                    'Option': 'Recursive',
                    'Values': [path]
                }
            ],
            MaxResults=50,
            NextToken=resp['NextToken']
        ) if 'NextToken' in resp else None
    
    count = 1
    lalas = []
    for i in items:
        getParameter = client.get_parameter(
                        Name = i['Name'],
                        WithDecryption=True
                    )
        if 'SecureString' in i['Type']:
            lalas.append({ "Name" : i['Name'], "Type": i['Type'],"Value": getParameter['Parameter']['Value'],"KeyId": i['KeyId']})

            #print "{\"Name\": \"%s\",\"Type\": \"%s\", \"Value\": \"%s\",\"KeyId\": \"%s\"}" % (i['Name'],i['Type'],getParameter['Parameter']['Value'],i['KeyId'])
        else:
            lalas.append({ "Name" : i['Name'], "Type": i['Type'],"Value": getParameter['Parameter']['Value']})
            #print "{\"Name\": \"%s\",\"Type\": \"%s\", \"Value\": \"%s\"}" % (i['Name'],i['Type'],getParameter['Parameter']['Value'])
        count = count+1
    
    data = json.dumps(lalas,indent=4,sort_keys=True)
    if args.fileout:
        fp = open(args.fileout,'w')
        fp.write(data)
        fp.close()
    else:
        print data