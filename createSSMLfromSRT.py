# ==================================================================================
# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ==================================================================================
#
# createSSMLfromSRT.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
# 
# Purpose: This code drives the process to create a basic SSML file based on the contents of the provided SRT file
#
# Change Log:
#          3/10/2020: Initial version
#
# ==================================================================================


import argparse
from datetime import datetime
from datetime import timedelta
import time
import json
import codecs
import re




# ==================================================================================
# Function: main function
# Purpose: After processing arguments for the file names, read the SRT input file, and write it out to the designated SSML file   
# Parameters: See arg parser arguments
#                 
# ==================================================================================

# Get the command line arguments and parse them
parser = argparse.ArgumentParser( prog='createSSMLfromSRT.py', description='Read a SRT file and write it out to as an SSML file')
parser.add_argument('-srtin', required=True, help='The SMRTfile to process')
parser.add_argument('-ssmlout', required=True, help='The SSML file to output')	
parser.add_argument('-pcttimepad', required=False, default='1.0', help='The % of padding to add to the SSML MAX Duration.  Default = 1 (100%)')	
args = parser.parse_args()

# print out parameters and key header information for the user
print( "==> createSSMLfomSRT.py <===\n")
print( "==> Parameters: ")
print( "\t>>> SRT File In: " + args.srtin )
print( "\t>>> SSML File Out: " + args.ssmlout )
print( "\t>>> % Time Padding: " + args.pcttimepad + " (%d%%)" % (float(args.pcttimepad) * 100))


#read the input file
print( "\n==> Reading " + args.srtin + "\n")

try:
	# Open a file for reading and read each line into a separate list entry
	with open(args.srtin, "r") as srtin:
		srtcontents = srtin.readlines()
	print( "\t>>> Read successful" )
	print( "\t>>> Closing " + args.srtin)		
	srtin.close()
		
	if srtin.closed:
		print( "\t>>>", args.srtin, " is closed\n")
	else:
		print( "\t>>>", args.srtin, " is NOT closed\n")
	
except IOError as error:
	# Could not read to file, exit gracefully
	print(error)
	sys.exit(-1)
	

# Strip out the \n and whitespace from each of the entries
srtlines = [x.strip() for x in srtcontents]
srtlines2 = []

# Now get rid of the SRT line number rows and the blank lines
for count in range( 0, len(srtlines)):
	if (srtlines[count].isnumeric() == False and (srtlines[count] != '')):
		srtlines2.append(srtlines[count])


# Create a new array that figures out how many seconds Polly should take to speak the translated text based on the SRT time encoding
srtlines3 = []

for count in range( 0, len(srtlines2)):

	# Align each line to the time encoding
	if "-->" in srtlines2[count]:
		
		# split up the time encoding line into a start time, and ending time
		temp = srtlines2[count].split()
		
		# get the start time datetime structure and determine the starting seconds
		starttime = datetime.strptime(temp[0],'%H:%M:%S,%f')
		starttimeseconds = float( (starttime.microsecond/1000000 + starttime.second) + starttime.minute*60 + starttime.hour*3600 )
		

		# get the ending time datetime structure and determine the ending seconds
		endingtime = datetime.strptime(temp[2],'%H:%M:%S,%f')
		endingtimeseconds = float( (endingtime.microsecond/1000000 + endingtime.second) + endingtime.minute*60 + endingtime.hour*3600 )

		#get the total seconds
		totalseconds = (endingtimeseconds - starttimeseconds) * float(args.pcttimepad)

		#create a phrase list and add the total seconds
		phrase = []
		phrase.append(  "%3.2f" % totalseconds )
		phrase.append( srtlines2[count + 1] )

		srtlines3.append( phrase )



#write the input file
print( "\n==> Writing " + args.ssmlout + "\n")

#create the SSML from the list of phrases 
ssml = "<speak>\n"


for phrase in srtlines3:

	#for each line in the SRT, create an SSML line that will be read back in the corresponding amount of time
	ssml += "<prosody amazon:max-duration=\"" + phrase[0] +  "\">" + phrase[1] + "</prosody>\n"


ssml += "</speak>"


try:
	# Open a file for writing and write out the whole SSML string
	ssmlout = codecs.open(args.ssmlout,"w+", "utf-8")
	ssmlout.write( str(ssml) )
	ssmlout.close()
		
		
	if ssmlout.closed:
		print( "\t>>>", args.ssmlout, " is closed\n")
	else:
		print( "\t>>>", args.ssmlout, " is NOT closed\n")
		
except IOError as error:
	# Could not write to file, exit gracefully
	print(error)
	sys.exit(-1)

print( "\n==> Processing Complete\n")
