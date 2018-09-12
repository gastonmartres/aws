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
import psutil

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
parser = argparse.ArgumentParser(description='Check free space on partitions. If any of them are above the defined threshold, then a notification is send via a SNS Topic.')
parser.add_argument('--profile',help="Set the profile to use when fetching or uploading parameters. \nIf no profile is provided, ENV variables and .aws/config is used by default.",default='default')
parser.add_argument('--debug',help="Debug mode, TODO", action="store_true",default=False)
parser.add_argument('--region',help='Sets the region from where to gather data. Defaults to us-east-1',default='us-east-1')
parser.add_argument('--config', help='Specify the config file.',type=str,required=True)
parser.add_argument('--dry-run', help='Checks everything that is supposed to, but doesn\'t really send any notification',action='store_true',default=False)

#parser.add_argument('--all',help="Apply the action to all instances in the config file",action='store_true',default=False)
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
	
	debug = args.debug
	
	if debug:
		print args

	alert = False
	partitions = config.get('configuration','partitions').split(',')
	flag_file = config.get('configuration','flag_file')
	do_notification = config.get('configuration','notification')
	threshold = config.get('configuration','threshold')
	resend_time = config.get('configuration','resend_time')
	send_logs = config.get('configuration','send_logs')
	log_group = config.get('configuration','log_group')
	log_stream = config.get('configuration','log_stream')
	msg = "\nThe following partition/s have free space problem/s:\n"
	dry_run = args.dry_run

	if debug:
		print "Checking the following partition/s: "
	for i in partitions:
		try:
			usage = psutil.disk_usage(i)
			if debug:
				print "\tPartition: %s, Threshold: %s, Used: %s" % (bold(i),threshold, usage[3])
			if int(usage[3]) >= int(threshold):
				alert = True
				msg = msg + "\tPartition: %s, Threshold: %s, Used: %s" % (bold(i),threshold, usage[3])
		except Exception,e:
			print "Error: %s" % (red(bold(e)))
	
	# Si entramos en estado de alerta
	if alert:			
		ts_now = str(int(time.time()))
		if debug:
			print msg
			print "Timestamp now: %s" % (green(ts_now))
		have_flag = False
		# Seccion de Flag File
		if os.path.exists(flag_file):
			if os.path.isfile(flag_file):
				fp = open(flag_file,'r')
				ts_file = fp.readline()
				if debug:
					print "Time in file: %s" % (yellow(ts_file))
				have_flag = True
		else:
			fp = open(flag_file,'w')
			fp.write(ts_now)
			fp.close
	
		# Notificacion via AWS SNS
		if do_notification == "True":
			# Si tenemos en True have_flag, hacemos chequeo de tiempo para reenviar mensaje por SNS
			if have_flag:			
				ts_diff = int(ts_now) - int(ts_file)
				if int(ts_diff) >= int(resend_time):
					if debug:
						print "We are past beyond resend time. Resending message."
						print "Diff: %s" % (yellow(ts_diff))
						print "Resend: %s" % (green(resend_time))

					#Creamos el pointer a la conexion de AWS
					if args.profile == 'default':
						try:
							session = boto3.Session(region_name=args.region)
							if debug:
								print "---=[ Connecting to AWS without a profile... ]=---"
						except Exception, e:
							print "[No Profile] - Error setting client connection: %s" % (red(str(e)))
							sys.exit(1)
					else:
						try:
							if debug:
								print "---=[ Connecting to AWS with profile %s ... ]=---" % (green(str(args.profile)))
							session = boto3.Session(profile_name=args.profile,region_name=args.region)
						except Exception, e:
							print "[Profile] - Error setting client connection: %s" % (red(str(e)))
							sys.exit(1)
					try:
						if dry_run:
							print "Not truly sending notification."
						else:
							client = session.client('sns')
							response = client.publish(
								TopicArn = config.get(args.profile,'topic_arn'),
								Message = msg,
								Subject = config.get('configuration','msg_subject')
							)
					except Exception,e:
						print "Error: %s" % (red(bold(e)))
						sys.exit(1)
					'''
					if send_logs == "True":
						try:
							client = session.client('logs')
							token_file = open('/tmp/token','r')
							token = token_file.readline().strip()
							print token
							response = client.put_log_events(
								logGroupName=log_group,
								logStreamName=log_stream,
								logEvents=[
									{
										'timestamp': int(ts_now),
										'message': msg
									},
								],
								sequenceToken=token
							)
							print response
						except Exception,e:
							print "Error (Logs): %s" % (red(bold(e)))
					'''
					try:
						os.unlink(flag_file)
						fp = open(flag_file,'w')
						fp.write(ts_now)
						fp.close
					except Exception,e:
						print "Error: %s" % (red(bold(e)))
					sys.exit(1)
				else:
					if debug:
						print "We still have space problems, but there is some time left until I can resend notifications."
						print "Diff: %s" % (yellow(ts_diff))
						print "Resend: %s" % (green(resend_time))
					sys.exit(1)
	else:
		sys.exit(0)
