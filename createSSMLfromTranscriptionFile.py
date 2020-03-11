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
# createSSMLfromTranscriptionFile.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
# 
# Purpose: 	This program reads a Transcription File and creates an SSML file from it directly
#			without going first to an SRT or VTT file
#
# Change Log:
#          03/10/20: Initial version
#
# ==================================================================================


import argparse
import time
import json
import codecs
import re
from datetime import datetime
from datetime import timedelta



# ==================================================================================
# Function: newPhrase
# Purpose: simply create a phrase tuple
# Parameters: 
#                 None
# ==================================================================================
def newPhrase():
	return { 'start_time': '', 'end_time': '', 'words' : [] }


	
# ==================================================================================
# Function: getTimeCode
# Purpose: Format and return a string that contains the converted number of seconds into SRT format
# Parameters: 
#                 seconds - the duration in seconds to convert to HH:MM:SS,mmm 
# ==================================================================================	
	# Format and return a string that contains the converted number of seconds into SRT format
def getTimeCode( seconds ):
	t_hund = int(seconds % 1 * 1000)
	t_seconds = int( seconds )
	t_secs = ((float( t_seconds) / 60) % 1) * 60
	t_mins = int( t_seconds / 60 )
	return str( "%02d:%02d:%02d,%03d" % (00, t_mins, int(t_secs), t_hund ))
	

# ==================================================================================
# Function: writeTranscriptToSRT
# Purpose: Function to get the phrases from the transcript and write it out to an SRT file
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 srtFileName - the name of the SRT file (e.g. "mySRT.SRT")
# ==================================================================================	
def writeTranscriptToSSML( transcript, sourceLangCode, ssmlFileName ):
	# Write the SRT file for the original language
	print( "==> Creating SSML from transcript")
	phrases = getPhrasesFromTranscript( transcript )
	writeSSML( phrases, ssmlFileName )
	
# ==================================================================================
# Function: getPhrasesFromTranscript
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the phrases from the translation 
#          and write it out to an SRT file
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
# ==================================================================================
def getPhrasesFromTranscript( transcript ):

	# This function is intended to be called with the JSON structure output from the Transcribe service.  However,
	# if you only have the translation of the transcript, then you should call getPhrasesFromTranslation instead

	# Now create phrases from the translation
	ts = json.loads( transcript )
	items = ts['results']['items']
	#print( items )
	
	#set up some variables for the first pass
	phrase =  newPhrase()
	phrases = []
	nPhrase = True
	x = 0
	c = 0

	print ("==> Creating phrases from transcript...")

	for item in items:

		# if it is a new phrase, then get the start_time of the first item
		if nPhrase == True:
			if item["type"] == "pronunciation":
				phrase["start_time"] = getTimeCode( float(item["start_time"]) )
				nPhrase = False
			c+= 1
		else:	
			# get the end_time if the item is a pronuciation and store it
			# We need to determine if this pronunciation or puncuation here
			# Punctuation doesn't contain timing information, so we'll want
			# to set the end_time to whatever the last word in the phrase is.
			if item["type"] == "pronunciation":
				phrase["end_time"] = getTimeCode( float(item["end_time"]) )
				
		# in either case, append the word to the phrase...
		phrase["words"].append(item['alternatives'][0]["content"])
		x += 1
		
		# now add the phrase to the phrases, generate a new phrase, etc.
		if x == 10:
			#print c, phrase
			phrases.append(phrase)
			phrase = newPhrase()
			nPhrase = True
			x = 0
			
	return phrases



# ==================================================================================
# Function: writeSSML
# Purpose: Iterate through the phrases and write them to the SSML file
# Parameters: 
#                 phrases - the array of JSON tuples containing the phrases to show up as subtitles
#                 filename - the name of the SRT output file (e.g. "mySRT.srt")
# ==================================================================================
def writeSSML( phrases, filename ):
	print ("==> Writing phrases to disk...")

	# open the files
	ssmlout = codecs.open(filename,"w+", "utf-8")
	x = 1
	
	ssml = "<speak>\n" 
	
	for phrase in phrases:

		# determine how many words are in the phrase
		length = len(phrase["words"])
		
		
		# get the start time datetime structure and determine the starting seconds
		starttime = datetime.strptime(phrase["start_time"],'%H:%M:%S,%f')
		starttimeseconds = float( (starttime.microsecond/1000000 + starttime.second) + starttime.minute*60 + starttime.hour*3600 )
		

		# get the ending time datetime structure and determine the ending seconds
		endingtime = datetime.strptime(phrase["end_time"],'%H:%M:%S,%f')
		endingtimeseconds = float( (endingtime.microsecond/1000000 + endingtime.second) + endingtime.minute*60 + endingtime.hour*3600 )

		#get the total seconds
		totalseconds = (endingtimeseconds - starttimeseconds) * float(args.pcttimepad)
		
		
		ssml += "<prosody amazon:max-duration=\"" + "%3.2f" % (totalseconds) +  "\">" + getPhraseText(phrase) + "</prosody>\n"
		
	
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



# ==================================================================================
# Function: getPhraseText
# Purpose: For a given phrase, return the string of words including punctuation
# Parameters: 
#                 phrase - the array of JSON tuples containing the words to show up as subtitles
# ==================================================================================

def getPhraseText( phrase ):

	length = len(phrase["words"])
		
	out = ""
	for i in range( 0, length ):
		if re.match( '[a-zA-Z0-9]', phrase["words"][i]):
			if i > 0:
				out += " " + phrase["words"][i]
			else:
				out += phrase["words"][i]
		else:
			out += phrase["words"][i]
			
	return out



# ==================================================================================
# Function: main function
# Purpose: After processing arguments for the file names, read the transcription input file, and write it out to the designated SRT file   
# Parameters: See arg parser arguments
#                 
# ==================================================================================

# Get the command line arguments and parse them
parser = argparse.ArgumentParser( prog='createSRTfromTranscriptionFile.py', description='Process a JSON transcription from AWS Transcribe and write it out to as an SRT file')
parser.add_argument('-transin', required=True, help='The transcription file to process')
parser.add_argument('-ssmlout', required=True, help='The SSML file to output')	
parser.add_argument('-pcttimepad', required=False, default='1.0', help='The % of padding to add to the SSML MAX Duration.  Default = 1 (100%)')	
args = parser.parse_args()

# print out parameters and key header information for the user
print( "==> createSSMLfomTranscriptionFile.py <===\n")
print( "==> Parameters: ")
print( "\t>>>Transcription File In: " + args.transin  )
print( "\t>>>SSML File Out: " + args.ssmlout )
print( "\t>>> % Time Padding: " + args.pcttimepad + " (%d%%)" % (float(args.pcttimepad) * 100))


#read the input file
print( "\n==> Reading " + args.transin + "\n")

try:
	# Open a file for reading the output as a binary stream
	with open(args.transin, "r") as tfile:
		transin = tfile.read()
	print( "\t>>> Read successful" )
	print( "\t>>> Closing " + args.transin)		
	tfile.close()
		
	if tfile.closed:
		print( "\t>>>", args.transin, " is closed\n")
	else:
		print( "\t>>>", args.transin, " is NOT closed\n")
	
except IOError as error:
	# Could not read to file, exit gracefully
	print(error)
	sys.exit(-1)
		
print( "==> Process Transcript\n")
# Now get the t# Create the SRT File for the original transcript and write it out.  
writeTranscriptToSSML( transin, 'en', args.ssmlout )  
print( "\n==> Processing Complete\n")
	




		
