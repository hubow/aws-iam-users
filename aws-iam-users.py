#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import botocore
import string
import random
import csv
import argparse

def parseArgs():
    parser = argparse.ArgumentParser(prog='aws-iam-users.py', usage='%(prog)s [options] or -h for help')
    parser.add_argument('--file', dest = 'file', required=True, help = 'Please specify csv file name containing following columns/header: team,email')
    parser.add_argument('--profile', dest = 'profile', required=True, help = 'Please specify AWS profile name configured in .aws/config, e.g.: playground')
    args = parser.parse_args()
    return args

def generatePass(length=22):
  symbols = '#$%&()*+-:<=>?@[]]^_'
  randDigit = random.choice(string.digits) 
  randUpper = random.choice(string.ascii_uppercase) 
  randLower = random.choice(string.ascii_lowercase) 
  randSymbol = random.choice(symbols) 
  requiredChars = randDigit + randUpper + randLower + randSymbol
  passChars = string.ascii_lowercase + string.ascii_uppercase + string.digits + symbols
  tempPass = requiredChars + ''.join(random.choice(passChars) for x in range(length-4))
  return tempPass

def choice(question):
  while True:
    choice = input(question + " [y/n]: ").lower()
    if choice[:1] == 'y': 
      return True
    elif choice[:1] == 'n':
      return False
    else:
      print('Please respond with \'Yes\' or \'No\'\n')

def createIamGroup(usergroup):
  if usergroup:
    try: 
      group = iamClient.get_group(GroupName=usergroup)
    except botocore.exceptions.ClientError as e:
      group = None
      if e.response['Error']['Code'] != "NoSuchEntity":
        raise
    if group:
      print('IAM Group %s already exists' % usergroup)
    else:
      iamClient.create_group(GroupName = newGroup)
      print('Group %s created' % usergroup)

def create_user(username, usergroup):
  user_info = {}
  user_info["username"] = username
  try:
    user = iamClient.get_user(UserName=username)

  except botocore.exceptions.ClientError as e:
    user = None
    if e.response['Error']['Code'] != "NoSuchEntity":
      raise
  if user:
    print('Username %s already exists' % username)
  else:
    user = iamClient.create_user(UserName=username)
    # print('user created')
  
  password = generatePass()
  # print(password)
  try:
    iamClient.create_login_profile(UserName=username, Password=password, PasswordResetRequired=True)
    user_info['password'] = password
  except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] != "EntityAlreadyExists":
      raise
    else:
      print('Password%s' % e.response['Error']['Code'])
      answer = choice('Do you want to update %s password?' % username)
      if answer == True:
        iamClient.update_login_profile(UserName=username, Password=password, PasswordResetRequired=True)
        user_info['password'] = password
      elif answer == False:
        print('Leaving password unchanged.')


  return user_info

def addUserToGroup(username, usergroup):
  group = iamResource.Group('employee')
  group.add_user(
    UserName=username
  )
  if usergroup:
    group = iamResource.Group(usergroup)
    group.add_user(
      UserName=username
    )

session = boto3.Session(profile_name=parseArgs().profile)
iamResource = session.resource('iam')
iamClient = session.client('iam')

fileName = parseArgs().file
csvFile = csv.reader(open("./%s" % (fileName)), delimiter=",")
next(csvFile, None)

for row in csvFile:
  newUser = row[1].split("@")[0]
  newGroup = row[0]
  groupsList = iamClient.list_groups()['Groups']
  createIamGroup(newGroup)
  createdUser = create_user(newUser, newGroup)
  print(createdUser)
  addUserToGroup(newUser, newGroup)
