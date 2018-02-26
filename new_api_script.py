import subprocess
import csv
import sys
import time
import requests
import json

#Getting serial number of ASA device from user input
serial_num = input("Enter Serial Number of ASA Device: ")

#Searching parameters.csv for specified Serial Number
with open('parameters.csv',newline='') as csvfile:
    reader = csv.reader(csvfile)
    found = 0
	#looping through parameters.csv to find record matching provided serial number
    for row in reader:
        if row[0]==serial_num:
            found = 1
            print("FOUND!...",row)

            hostname = row[1]
            outside_ip = row[2] 
            outside_mask = row[3]
            inside_ip = row[4]
            inside_mask = row[5]
            gateway_ip = row[6]
            gateway_mask = row[7]
            sfr_ip = row[8]
            sfr_mask = row[9]
            sfr_domain = row[10]
            sfr_password = row[11]
            sfr_device_name = row[12]
            fmc_ip = row[13]
            fmc_user = row[14]
            fmc_password = row[15]
            fmc_devicegroup_name = row[16]
            fmc_policy_name = row[17]
            break
    if not found:
        print("Serial number was not found in csv... Please re-run this script to try again")
        sys.exit()

server = "https://"+fmc_ip
username = fmc_user
password = fmc_password

if len(sys.argv) > 1:
    username = sys.argv[1]
if len(sys.argv) > 2:
    password = sys.argv[2]
               
r = None
headers = {'Content-Type': 'application/json'}
api_auth_path = "/api/fmc_platform/v1/auth/generatetoken"
auth_url = server + api_auth_path
try:
	# 2 ways of making a REST call are provided:
	# One with "SSL verification turned off" and the other with "SSL verification turned on".
	# The one with "SSL verification turned off" is commented out. If you like to use that then 
	# uncomment the line where verify=False and comment the line with =verify='/path/to/ssl_certificate'
	# REST call with SSL verification turned off: 
	r = requests.post(auth_url, headers=headers, auth=requests.auth.HTTPBasicAuth(username,password), verify=False)
	# REST call with SSL verification turned on: Download SSL certificates from your FMC first and provide its path for verification.
	#r = requests.post(auth_url, headers=headers, auth=requests.auth.HTTPBasicAuth(username,password), verify='/path/to/ssl_certificate')
	auth_headers = r.headers
	auth_token = auth_headers.get('X-auth-access-token', default=None)
	if auth_token == None:
		print("auth_token not found. Exiting...")
		sys.exit()
except Exception as err:
	print ("Error in generating auth token --> "+str(err))
	sys.exit()
headers['X-auth-access-token']=auth_token

def fmc_api_post(api_url,post_obj):
	try:
		# REST call with SSL verification turned off:
		r = requests.post(api_url, data=json.dumps(post_obj), headers=headers, verify=False)
		# REST call with SSL verification turned on:
		#r = requests.post(url, data=json.dumps(post_data), headers=headers, verify='/path/to/ssl_certificate')
		status_code = r.status_code
		resp = r.text
		print("Status code is: "+str(status_code))
		if status_code == 201 or status_code == 202:
			print ("Post was successful...")
			json_resp = json.loads(resp)
			print(json.dumps(json_resp,sort_keys=True,indent=4, separators=(',', ': ')))
		else :
			r.raise_for_status()
			print ("Error occurred in POST --> "+resp)
			json_resp = None
	except requests.exceptions.HTTPError as err:
		print ("Error in connection --> "+str(err))
	finally:
		if r: r.close()
	return json_resp

def fmc_api_get(api_url):
	try:
		# REST call with SSL verification turned off: 
		r = requests.get(api_url, headers=headers, verify=False)
		# REST call with SSL verification turned on:
		#r = requests.get(url, headers=headers, verify='/path/to/ssl_certificate')
		status_code = r.status_code
		resp = r.text
		if (status_code == 200):
			print("GET successful. Response data --> ")
			json_resp = json.loads(resp)
			print(json.dumps(json_resp,sort_keys=True,indent=4, separators=(',', ': ')))
		else:
			r.raise_for_status()
			print("Error occurred in GET --> "+resp)
			json_resp = None
	except requests.exceptions.HTTPError as err:
		print ("Error in connection --> "+str(err)) 
	finally:
		if r : r.close()	
	return json_resp

print("Starting API Calls...")

# GET ACCESS POLICY OPERATION
api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/policy/accesspolicies?name="+fmc_policy_name
url = server + api_path
if (url[-1] == '/'):
	url = url[:-1]
print("GETting ID of Access Policy "+fmc_policy_name+"...")
policy_obj=fmc_api_get(url)
policy_id=policy_obj['items'][0]['id']

#SEARCH FOR PROVIDED DEVICE GROUP 
api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/devicegroups/devicegrouprecords"
url = server + api_path
if (url[-1] == '/'):
	url = url[:-1]
print("Searching for device group " + fmc_devicegroup_name + "...")
group_search=fmc_api_get(url)
if("items" in group_search):
	group_index=0
	device_group_id=None
	for dg in group_search['items']:
		if(dg['name']==fmc_devicegroup_name):
			print("FOUND device group with name of " + fmc_devicegroup_name)
			device_group_id = dg['id']
			break
else:
	print("Provided device group name NOT FOUND, creating device group " + fmc_devicegroup_name)
	# POST/CREATE DEVICE GROUP OPERATION
	api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/devicegroups/devicegrouprecords"
	url = server + api_path
	if (url[-1] == '/'):
		url = url[:-1]
	post_data = {
		"name": fmc_devicegroup_name,
	}
	print("POSTing device group " + fmc_devicegroup_name+"...")
	group_obj = fmc_api_post(url,post_data)
	device_group_id = group_obj['id']

# POST/CREATE DEVICE OPERATION
api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/devices/devicerecords"
url = server + api_path
if (url[-1] == '/'):
	url = url[:-1]

post_data = {
	"name": sfr_device_name,
	"hostName": sfr_ip,
	"regKey": "C1sc0123",
	"type": "Device",
	"license_caps": [
		"MALWARE",
		"URLFilter",
		"PROTECT",
		"CONTROL",
		"VPN"
	],
	"deviceGroup": {
		"id": device_group_id
	},
	"accessPolicy": {
		"id": policy_id
	}
}
print("POSTing device " + sfr_device_name + " and adding to group " + fmc_devicegroup_name + " and assigning to policy " + fmc_policy_name + "...")
device_obj = fmc_api_post(url,post_data)

print("YOU HAVE JUST WITNESSED THE POWER OF RAPIDFIRE... SHOCK AND AWE EFFECTS MAY OR MAY NOT SUBSIDE BY THE TIME THE FMC FINISHES ITS PART OVER THE NEXT 10-15 MINUTES")