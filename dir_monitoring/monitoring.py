#!/usr/bin/env python

# This script looks into a directory and checks if
# some files have changed since last execution

from stat import S_ISREG, ST_CTIME, ST_MODE
import os, time
import pickle
import subprocess
from datetime import datetime
import json

dirPath = "/dir_monitoring/to_monitor"
savePath = "/dir_monitoring/tmp/files.pkl"
indexFile = "/dir_monitoring/htdocs/index.json"

time_to_sleep = 60 # Time in seconds between two executions

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output)

# Make a system call
def system_call(command, from_docker=True):
	if from_docker:
		command = "docker exec ipfs-container " + command
	print("Executing: ", command)
	p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
	return p.stdout.read()

print("--------------------------")
print("Welcome to IPFS monitoring")
print("--------------------------")

# Wait for other containers to start
time.sleep(10)

# Main loop
while True:

	print("--------------------------------------")
	print("IPFS monitoring")
	print("Looking for modifications in directory")

	##############################
	# Load current IPFS state
	##############################
	try:
		with open(savePath, 'rb') as input:
		    currentIPFSState = pickle.load(input)
	except FileNotFoundError:
		# First launch: initialize currentIPFSState to empty dict
		currentIPFSState = {}

	##############################
	# Scan monitored directory
	##############################

	# get all entries in the directory w/ stats
	entries = (os.path.join(dirPath, fn) for fn in os.listdir(dirPath))
	entries = ((os.stat(path), path) for path in entries)

	# leave only regular files, insert creation date
	entries = [(stat[ST_CTIME], path)
	           for stat, path in entries if S_ISREG(stat[ST_MODE])]


	###############################
	# Compare curent IPFS state
	# with directory state
	###############################

	# Select IPFS files that have been modified or removed
	filesToRemove = [mHash for mHash in currentIPFSState if currentIPFSState[mHash] not in entries]

	# Select IPFS files that have been modified or removed
	filesToAdd = [f for f in entries if f not in currentIPFSState.values()]

	################################
	# Record changes in IPFS
	################################

	# Remove old files from IPFS
	print ("Removing files from IPFS...")
	count = 0
	for mHash in filesToRemove:
		count += 1
		# Remove file from ipfs
		print("Removing file from IPFS: ", mHash, currentIPFSState[mHash][1])
		response = system_call("ipfs pin rm " + mHash)
		print (response.strip().decode('UTF-8'))
		# Remove file from dictionary
		currentIPFSState.pop(mHash, None)

	print("%i files removed." % count)

	# Add new files to IPFS
	print ("Adding files to IPFS...")
	count = 0
	for f in filesToAdd:
		count += 1
		# Add file to ipfs
		print("Adding file: ", f[1])
		mHash = system_call("ipfs add -q " + f[1])
		mHash = mHash.strip().decode('UTF-8')
		print (mHash)
		currentIPFSState[mHash] = f

	print ("%i files added." % count)

	#################################
	# Save new IPFS state in file
	#################################

	print ("Saving new state...")
	save_object(currentIPFSState, savePath)

	######################################
	# Create index file with new state
	######################################

	print ("Saving index file: %s" % indexFile)
	index = [{	'hash': mHash,
				'file': currentIPFSState[mHash][1],
				'uploaded_at': datetime.utcfromtimestamp(currentIPFSState[mHash][0]).strftime('%Y-%m-%dT%H:%M:%SZ')}
				for mHash in currentIPFSState]

	with open(indexFile, 'w') as outfile:
	    json.dump(index, outfile)

	print ("IPFS monitoring going to sleep for %d seconds" % time_to_sleep)
	print ("-----------------------------------------------------")

	#####################################
	# Sleep for some time
	#####################################
	time.sleep(time_to_sleep)