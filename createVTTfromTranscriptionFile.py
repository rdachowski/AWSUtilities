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
# createVTTFromTransciptionFile.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
# 
# Purpose: This code drives the process to create a transription job, translate it into another language,
#          create subtitles, use Amazon Polly to synthesize an alternate audio track, and finally put it all together
#          into a new video.
#
# Change Log:
#          6/29/2018: Initial version
#
# ==================================================================================


import argparse
import time
import json
import codecs
import re




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
# Purpose: Format and return a string that contains the converted number of seconds into VTT format
# Parameters: 
#                 seconds - the duration in seconds to convert to HH:MM:SS,mmm 
# ==================================================================================	
	# Format and return a string that contains the converted number of seconds into VTT format
def getTimeCode( seconds ):
	t_hund = int(seconds % 1 * 1000)
	t_seconds = int( seconds )
	t_secs = ((float( t_seconds) / 60) % 1) * 60
	t_mins = int( t_seconds / 60 )
	return str( "%02d:%02d:%02d.%03d" % (00, t_mins, int(t_secs), t_hund ))
	

# ==================================================================================
# Function: writeTranscriptToVTT
# Purpose: Function to get the phrases from the transcript and write it out to an VTT file
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 VTTFileName - the name of the VTT file (e.g. "myVTT.VTT")
# ==================================================================================	
def writeTranscriptToVTT( transcript, sourceLangCode, VTTFileName, fstyle ):
	# Write the VTT file for the original language
	print( "==> Creating VTT from transcript")
	phrases = getPhrasesFromTranscript( transcript )
	writeVTT( phrases, VTTFileName, fstyle )
	
# ==================================================================================
# Function: getPhrasesFromTranscript
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the phrases from the translation 
#          and write it out to an VTT file
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
# Function: writeVTT
# Purpose: Iterate through the phrases and write them to the VTT file
# Parameters: 
#                 phrases - the array of JSON tuples containing the phrases to show up as subtitles
#                 filename - the name of the VTT output file (e.g. "myVTT.VTT")
# ==================================================================================
def writeVTT( phrases, filename, fstyle ):
	print ("==> Writing phrases to disk...")

	# open the files
	e = codecs.open(filename,"w+", "utf-8")
	x = 1
	
	# write the header of the webVTT file
	e.write( "WEBVTT\n\n")
	
	for phrase in phrases:

		# determine how many words are in the phrase
		length = len(phrase["words"])
		
		# write out the phrase number
		e.write( str(x) + "\n" )
		x += 1
		
		# write out the start and end time
		e.write( phrase["start_time"] + " --> " + phrase["end_time"] + " " + fstyle + "\n" )
					
		# write out the full phase.  Use spacing if it is a word, or punctuation without spacing
		out = getPhraseText( phrase )

		# write out the WebVTT file
		e.write(out + "\n\n" )
		
	e.close()


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
# Purpose: After processing arguments for the file names, read the transcription input file, and write it out to the designated VTT file   
# Parameters: See arg parser arguments
#                 
# ==================================================================================

# Get the command line arguments and parse them
parser = argparse.ArgumentParser( prog='createVTTfromTranscriptionFile.py', description='Process a JSON transcription from AWS Transcribe and write it out to as an VTT file')
parser.add_argument('-transin', required=True, help='The transcription file to process')
parser.add_argument('-vttout', required=True, help='The VTT file to output')		
parser.add_argument('-fstyle', required=True, help='The style for subtitles to appear on screen.  E.g. "A:middle L:90%"')
args = parser.parse_args()

# print out parameters and key header information for the user
print( "==> createVTTfromTranscriptionFile.py <===\n")
print( "==> Parameters: ")
print( "\t>>>Transcription File In: " + args.transin  )
print( "\t>>>VTT File Out: " + args.vttout )
print( "\t>>>Format Style: " + args.fstyle )


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
# Now get the t# Create the VTT File for the original transcript and write it out.  
writeTranscriptToVTT( transin, 'en', args.vttout, args.fstyle )  
print( "\n==> Processing Complete\n")
	




		
