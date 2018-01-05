import subprocess
import csv
import sys
import time


serial_num = input("Enter Serial Number: ")

with open('parameters.csv',newline='') as csvfile:
    reader = csv.reader(csvfile)
    found = 0

    for row in reader:
        if row[0]==serial_num:
            found = 1
            print("FOUND!....",row)

            hostname = row[1]
            outside_ip = row[2]
            inside_ip = row[3]
            gateway_ip = row[4]
            mgmt_ip = row[5]
            break

    if not found:
        print("Serial number was not found in csv... Please re-run this script to try again")
        sys.exit()

print("Calling subprocess...")
subprocess.call(["screen","-d","-m","-S","cisco2","/dev/ttyUSB0"])
subprocess.call(["screen","-S","cisco2","-X","stuff","no\r\ren\r\rconf t\rhostname "+hostname+"\rexit\rsession sfr console\r"],stdout=subprocess.PIPE)
time.sleep(15)
subprocess.call(["screen","-S","cisco2","-X","stuff","\r\radmin\r"],stdout=subprocess.PIPE)
time.sleep(2)
subprocess.call(["screen","-S","cisco2","-X","stuff","Admin123\r"],stdout=subprocess.PIPE)
time.sleep(10)
subprocess.call(["screen","-S","cisco2","-X","stuff","\r"],stdout=subprocess.PIPE)
time.sleep(2)
subprocess.call(["screen","-S","cisco2","-X","stuff","q\yes\r"],stdout=subprocess.PIPE)
time.sleep(10)
subprocess.call(["screen","-S","cisco2","-X","stuff","C1sc0123\rC1sc0123\r"],stdout=subprocess.PIPE)
time.sleep(5)
subprocess.call(["screen","-S","cisco2","-X","stuff","\r\r\r"+mgmt_ip+"\r255.255.255.0\r"+gateway_ip+"\r\r\rcisco.com\r"],stdout=subprocess.PIPE)
time.sleep(5)
subprocess.call(["screen","-S","cisco2","-X","stuff","\r"],stdout=subprocess.PIPE)

#output = process.communicate()[0]
#output.stdout.decode('utf-8')
#print(format(output))
