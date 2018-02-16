import subprocess
import csv
import sys
import time
import requests
import json

#Getting serial number of ASA device from user input
serial_num = input("Enter Serial Number: ")

with open('parameters.csv',newline='') as csvfile:
    reader = csv.reader(csvfile)
    found = 0
	#looping through parameters.csv to find record matching provided serial number
    for row in reader:
        if row[0]==serial_num:
            found = 1
            print("FOUND!....",row)

            hostname = row[1]
            outside_ip = row[2]
            outside_mask = row[3]
            inside_ip = row[4]
            inside_mask = row[5]
            gateway_ip = row[6]
            gateway_mask = row[7]
            sfr_ip = row[8]
            break

    if not found:
        print("Serial number was not found in csv... Please re-run this script to try again")
        sys.exit()

print("Calling subprocess...")
#Creating screen session to consoled device
subprocess.call(["screen","-d","-m","-S","cisco","/dev/ttyUSB0"])
#applying hostname and IP information to device and starting session with sfr module
subprocess.call(["screen","-S","cisco","-X","stuff","no\r\ren\r\rconf t\rhostname "+hostname+"\rinterface man 1/1\rno shut\rnameif management\rinterface gigabitethernet 1/1\rno shut\rnameif outside\rip address "+outside_ip+" "+outside_mask+"\r\rinterface gigabitethernet 1/2\rno shut\rnameif inside\rip address "+inside_ip+" "+inside_mask+"\rexit\rroute outside 0.0.0.0 0.0.0.0 "+gateway_ip+"\rexit\rsession sfr console\r"],stdout=subprocess.PIPE)
print("Waiting 30 sec to let SFR module load")
time.sleep(30)
#logging in as admin
subprocess.call(["screen","-S","cisco","-X","stuff","\r\radmin\r"],stdout=subprocess.PIPE)
time.sleep(2)
#providing default admin password
subprocess.call(["screen","-S","cisco","-X","stuff","Admin123\r"],stdout=subprocess.PIPE)
time.sleep(10)
#return to start EULA agreement
subprocess.call(["screen","-S","cisco","-X","stuff","\r"],stdout=subprocess.PIPE)
time.sleep(2)
#skipping scroll through EULA agreement
subprocess.call(["screen","-S","cisco","-X","stuff","q"],stdout=subprocess.PIPE)
time.sleep(2)
#agreeing to EULA agreement
subprocess.call(["screen","-S","cisco","-X","stuff","YES\r"],stdout=subprocess.PIPE)
time.sleep(2)
#providing new password to sfr module
subprocess.call(["screen","-S","cisco","-X","stuff","C1sc0123\rC1sc0123\r"],stdout=subprocess.PIPE)
time.sleep(10)
#accepting default config values
subprocess.call(["screen","-S","cisco","-X","stuff","\r\r\r"],stdout=subprocess.PIPE)
time.sleep(1)
#providing mgmt IP to sfr module
subprocess.call(["screen","-S","cisco","-X","stuff",""+sfr_ip+"\r"],stdout=subprocess.PIPE)
time.sleep(1)
#providing subnet value for sfr module
subprocess.call(["screen","-S","cisco","-X","stuff","255.255.255.0\r"],stdout=subprocess.PIPE)
time.sleep(1)
#providing gateway IP for sfr module
subprocess.call(["screen","-S","cisco","-X","stuff",""+gateway_ip+"\r"],stdout=subprocess.PIPE)
time.sleep(1)
#providing DNS IP for sfr module
subprocess.call(["screen","-S","cisco","-X","stuff","\r8.8.8.8\r"],stdout=subprocess.PIPE)
time.sleep(1)
#providing domain name for sfr module
subprocess.call(["screen","-S","cisco","-X","stuff","cisco.com\r"],stdout=subprocess.PIPE)
time.sleep(1)
#accepting agreeing to complete initial setup
subprocess.call(["screen","-S","cisco","-X","stuff","\r\r"],stdout=subprocess.PIPE)
time.sleep(160)
#configuring IP of FMC manager device to register with
subprocess.call(["screen","-S","cisco","-X","stuff","configure manager add 192.168.10.20 C1sc0123\r"],stdout=subprocess.PIPE)

print("Sleeping 30 sec before API calls")

time.sleep(30)

server = "https://192.168.10.20"
username = "api"
password = "C1sc0123"

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
	except requests.exceptions.HTTPError as err:
		print ("Error in connection --> "+str(err)) 
	finally:
		if r : r.close()	
	return json_resp

# GET ACCESS POLICY OPERATION
api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/policy/accesspolicies?name=DRC-Access-Policy"
url = server + api_path
if (url[-1] == '/'):
	url = url[:-1]
policy_obj=fmc_api_get(url)
policy_id=policy_obj['items'][0]['id']

# POST/CREATE DEVICE GROUP OPERATION
api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/devicegroups/devicegrouprecords"
url = server + api_path
if (url[-1] == '/'):
    url = url[:-1]
post_data = {
	"name": "DRC",
}
group_obj = fmc_api_post(url,post_data)

# POST/CREATE DEVICE OPERATION
api_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/devices/devicerecords"
url = server + api_path
if (url[-1] == '/'):
	url = url[:-1]

post_data = {
	"name": "Houston",
	"hostName": "192.168.10.10",
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
		"id": group_obj['id']
	},
	"accessPolicy": {
		"id": policy_id
	}
}
device_obj = fmc_api_post(url,post_data)
