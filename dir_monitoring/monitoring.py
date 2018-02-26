#!/usr/bin/env python

# This script looks into a directory and checks if
# some files have changed since last execution

from stat import S_ISREG, ST_CTIME, ST_MODE
import os, time
import pickle
import subprocess
from datetime import datetime
import json
import ipfsapi

dirPath = "/dir_monitoring/to_monitor"
savePath = "/dir_monitoring/tmp/files.pkl"
indexFile = "/dir_monitoring/htdocs/index.json"

time_to_sleep = 60 # Time in seconds between two executions

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output)

print("--------------------------")
print("Welcome to IPFS monitoring")
print("--------------------------")

# Wait for other containers to start
time.sleep(10)

api = ipfsapi.connect('ipfs', 5001)

##############################
# Load current IPFS state
##############################
try:
	with open(savePath, 'rb') as input:
	    currentIPFSState = pickle.load(input)
except FileNotFoundError:
	# First launch: initialize currentIPFSState to empty dict
	currentIPFSState = {}

# Main loop
while True:

	print("--------------------------------------")
	print("IPFS monitoring")
	print("Looking for modifications in directory")

	##############################
	# Scan monitored directory
	##############################

	# get all entries in the directory w/ stats
	entries = ((os.path.join(dirPath, fn), fn) for fn in os.listdir(dirPath))
	entries = ((os.stat(path), path, fn) for path, fn in entries)

	# leave only regular files, insert creation date
	entries = [(stat[ST_CTIME], path, fn)
	           for stat, path, fn in entries if S_ISREG(stat[ST_MODE])]


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
		# This test protects again empty hash which may cause a freeze in system_call
		if mHash != "":
			count += 1
			# Remove file from ipfs
			print("Removing file from IPFS: ", mHash, currentIPFSState[mHash][1])
			response = api.pin_rm(mHash)
			print (response)
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
		try:
			res = api.add(f[1])
			mHash = res['Hash']
			print (mHash, f)
			currentIPFSState[mHash] = f
		except:
			print("Error in adding file to IPFS")

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
				'file': currentIPFSState[mHash][2],
				'uploaded_at': datetime.utcfromtimestamp(currentIPFSState[mHash][0]).strftime('%Y-%m-%dT%H:%M:%SZ')}
				for mHash in currentIPFSState]

	with open(indexFile, 'w') as outfile:
	    json.dump(index, outfile)


	#####################################
	# Garbage collect IPFS datastore
	#####################################
	
	print ("Launching IPFS garbage collector")

	print ("Repo stats before garbage collection:")
	print (api.repo_stat())

	result_gc = api.repo_gc()
	print ("Result of garbage collection:")
	print (result_gc)

	print ("Repo stats after garbage collection:")
	print (api.repo_stat())

	#####################################
	# Sleep for some time
	#####################################
	
	print ("IPFS monitoring going to sleep for %d seconds" % time_to_sleep)
	print ("-----------------------------------------------------")
	
	time.sleep(time_to_sleep)
