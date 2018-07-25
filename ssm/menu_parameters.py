#!/usr/bin/python
#  -*- coding: utf-8 -*-
# Author: Gaston Martres <gastonmartres@gmail.com>
# What it does: Just a simple script that lets you see what parameters are 
# configured in a determined path that you specify.
# 
# TODO: 
# - Use a menu system like with urwid.
# - Check for needed libraries.
# - Iter when there are more than 50 results.
# - Input validation

import boto3
import argparse
#import json
import locale
import sys
#import os
#import time
#import urwid

locale.setlocale(locale.LC_ALL,'es_AR.UTF-8')

# Parser de parametros
parser = argparse.ArgumentParser(description='App to put/get parameters from SSM/Parameter Store in AWS.')
parser.add_argument('--profile',help="Set the profile to use when fetching or uploading parameters. \nIf no profile is provided, ENV variables and .aws/config is used by default.")
parser.add_argument('--debug',help="Debug mode, TODO", action="store_true",default=False)
parser.add_argument('--region',help='Sets the region from where to gather data. Defaults to us-east-1',default='us-east-1')
parser.add_argument('--path', help='Sets the path from where to look for parameters',required=True)
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

def getParameterValue(parameter):
    print "De aca buscamos el parametro %s" % parameter


if __name__ == "__main__" :
    paramsReload = True
    error = False
    #Algunas validaciones antes de empezar.
    if args.path.endswith("/"):
        path = args.path
    else:
        path = args.path + "/"

    #Creamos el pointer a la conexion de AWS
    if args.profile == None:
        try:
            client = boto3.client('ssm',region_name=args.region)
            print "\n---=[ Connecting to AWS without a profile... ]=---"
        except Exception, e:
            print "Error setting client connection: %s" % (red(str(e)))
            sys.exit(1)
    else:
        try:
            print "\n---=[ Connecting to AWS with profile %s ... ]=---" % (green(str(args.profile)))
            session = boto3.Session(profile_name=args.profile,region_name=args.region)
            client = session.client('ssm') 
        except Exception, e:
            print "Error setting client connection: %s" % (red(str(e)))
            sys.exit(1)  

    while True:
        if paramsReload:
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
            count = 0
            parameter = []
            for i in resp['Parameters']:     
                print "%s: %s" % (str(count),i['Name'])
                if 'SecureString' in i['Type']:
                    data = {'Name':i['Name'],'Type': i['Type'],"KeyId": i['KeyId']}
                else:
                    data = {'Name':i['Name'],'Type': i['Type']}
                parameter.append(data)
                count = count+1
            paramsReload = False

        #action = str(raw_input("Enter ID to view it, N to add, M to modify, L to list, Q to quit: "))
        action = str(raw_input(bold("\nEnter (V)iew,(N)ew,(M)odify,(L)ist,(R)eload,(Q)uit: ")))
        
        # Salir
        if action in ('q','Q'):
            print "Exiting..."
            sys.exit(0)

        # Listar parametros
        if action in ('l','L'):
            lcount = 0
            for i in resp['Parameters']:     
                print "%s: %s" % (str(lcount),i['Name'])
                lcount = lcount + 1
        # Nuevo parametro
        elif action in ('n','N'):
            newParameterName = str(raw_input("Enter new parameter name %s: " % green(path)))
            newParameterData = str(raw_input("Enter new parameter value: "))
            typeParameter = str(raw_input("\nEnter Type: 1) String, 2) SecureString: "))
            # Veremos que hacemos con esto.
            # typeParameter = str(raw_input("Enter Type: 1) String, 2) SecureString, 3) StringList: "))
            #
            if typeParameter.isdigit:
                if typeParameter in ('1'):
                    selectTypeParameter = 'String'
                elif typeParameter in ('2'):
                    selectTypeParameter = 'SecureString'
                    keyIdParameter = str(raw_input("Enter KeyId: "))
                elif typeParameter in ('3'):
                    selectTypeParameter = 'StringList'
                else:
                    print "Aborted"
                    continue
            if typeParameter in ('2'):
                print "New parameter \"%s\", type \"%s\" (KeyId %s) with value \"%s\"" % (newParameterName,selectTypeParameter,keyIdParameter,newParameterData)    
            else:
                print "New parameter \"%s\", type \"%s\" with value \"%s\"" % (newParameterName,selectTypeParameter,newParameterData)
            is_ok = str(raw_input("Is this Ok? (y/n) "))
            try:
                if typeParameter in ('2'):
                    putParameter = client.put_parameter(
                        Name=path + newParameterName,
                        Value=newParameterData,
                        Type=selectTypeParameter,
                        KeyId=keyIdParameter,
                        Overwrite=True
                    )
                else:
                    putParameter = client.put_parameter(
                        Name=path + newParameterName,
                        Value=newParameterData,
                        Type=selectTypeParameter,
                        Overwrite=True
                    )
                print "Version: %s" % putParameter['Version']
                paramsReload = True
            except Exception,e:
                print "Could not put parameter: %s " % (bold(red(e)))
        # Modificamos parametros
        elif action in ('m','M'):
            wichParameter = str(raw_input("Enter ID: "))
            dataParameter = str(raw_input("Enter new value: "))
            print "Will put data \"%s\" into parameter %s" % (dataParameter,parameter[int(wichParameter)]['Name'])
            is_ok = str(raw_input("Is this Ok? (y/n) "))
            if is_ok in ('y','Y'):
                try:
                    if 'SecureString' in parameter[int(wichParameter)]['Type']:
                        putParameter = client.put_parameter(
                            Name=parameter[int(wichParameter)]['Name'],
                            Value=dataParameter,
                            Type=parameter[int(wichParameter)]['Type'],
                            KeyId=parameter[int(wichParameter)]['KeyId'],
                            Overwrite=True
                        )
                    else:
                        putParameter = client.put_parameter(
                            Name=parameter[int(wichParameter)]['Name'],
                            Value=dataParameter,
                            Type=parameter[int(wichParameter)]['Type'],
                            Overwrite=True
                        )
                    print "Version: %s" % putParameter['Version']
                except Exception,e:
                    print "Could not put parameter: %s " % (bold(red(e)))
            elif is_ok in ('n','N'):
                print "Aborted..."
                continue
            else:
                print "Aborted"
                continue
        # Reload de parametros.
        # Seteamos la variable paramsReload en True, para que al inicio del while traiga la data desde AWS 
        elif action in ('r','R'):
            paramsReload = True
            continue
        # Ver el contenido de un parametro.
        # Indicamos despues el ID numerico.
        elif action in ('v','V'):
            nroParameter = str(raw_input("Enter #ID: "))
            if nroParameter.isdigit():
                getParameter = client.get_parameter(
                        Name = parameter[int(nroParameter)]['Name'],
                        WithDecryption=True
                    )
                print "%s: %s" % (getParameter['Parameter']['Name'],getParameter['Parameter']['Value'])
            else:
                print "Enter number id."
                continue
        else:
            print "Don't try to fool me kid, or you'll gonna pay it..."