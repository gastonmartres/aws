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
parser = argparse.ArgumentParser(description='App to put/get parameters from SSM/Parameter Store in AWS.')
parser.add_argument('--filein',help="Json source file.",required=True)
parser.add_argument('--profile',help="Set the profile to use when fetching or uploading parameters. \nIf no profile is provided, ENV variables and .aws/config is used by default.")
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
    
    # Seccion para subir parametros a PS 
    if args.filein == None:
        print "Input file needed."
        sys.exit(1)

    if not os.path.isfile(args.filein):
        print bold(red("\n[ERROR]"))
        print "The file %s does not exists or not in current directory.\n" % (yellow(args.filein))
        sys.exit(1)
        
    with open(args.filein) as json_data:
        data = json.load(json_data)

    # Loop para ingresar parametros
    for i in data:
        try:
            i['KeyId']
            if args.debug:
                print "---= Inserting parameter =---"
                print "  Name: %s" % (green(str(i['Name'])))
                print "  Type: %s" % (yellow(str(i['Type'])))
                print " Value: %s" % (blue(str(i['Value'])))
                print " KeyId: %s" % (blue(str(i['KeyId'])))
            try:
                response = client.put_parameter(
                    Name=i['Name'],
                    Value=i['Value'],
                    Type=i['Type'],
                    KeyId=i['KeyId'],
                    Overwrite=True,
                )
                if args.debug:
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        print "----"
                        print " Parameter %s inserted successfuly." % (green(str(i['Name'])))

            except Exception, e:
                error = True
                print bold(red(" [ERROR]"))
                print " Cannot put parameter: %s" % (yellow(str(e)))
            
            time.sleep(1)
        except  KeyError:
            if args.debug:
                print "---= Inserting parameter =---"
                print "  Name: %s" % (green(str(i['Name'])))
                print "  Type: %s" % (yellow(str(i['Type'])))
                print " Value: %s" % (blue(str(i['Value'])))

            try:    
                response = client.put_parameter(
                    Name=i['Name'],
                    Value=i['Value'],
                    Type=i['Type'],
                    Overwrite=True,
                )
                if args.debug:
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        print "----"
                        print "Parameter %s inserted successfuly." % (green(str(i['Name'])))
                

            except Exception,e:
                error = True
                print bold(red(" [ERROR]"))
                print " Cannot put parameter: %s" % (yellow(str(e)))
            time.sleep(1)

    if error:
        print "\nThere were errors inserting parameters in PS, please review your configuration."
        print "\nExiting...\n"
        sys.exit(1)
    else:
        print "\nExiting...\n"
        sys.exit(0)
