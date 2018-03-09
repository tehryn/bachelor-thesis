#!/usr/bin/env python3

## @package rss_collect
# Collect and prepare url for download
# author: Matejka Jiri (xmatej52)
# school: VUT Brno, FIT
# module: collect.py
# python: python 3.4.2
# last modified: June 22, 2015

# TODO
# Komentare k __main__
import sys, os
from time import gmtime, strftime
from urllib.request import urlopen
import xml.etree.ElementTree as ET

## Prints help on stdout
def print_help():
	sys.stdout.write(
		"Usage ./collect.py [-o OUTPUT_FILE] [-a] [-i INPUT_FILE] [-c] [-e ERRORS_LOG_FILE]\n"
		"Download web pages and save them as ZipFile\n"
		"   -i      --input     input file with urls (stdin is default)\n"
		"   -o      --output    name of output ZipFile archive\n"
		"   -e      --errors    if set, errors will be print into this file (stderr is default)\n"
		"   -a      --append    if set, output file will be open in 'a' mode (new urls will be added at the end of a file)\n"
		"   -d      --dedup     folder where are located files with urls, that will not be included on output\n"
	)
	return None
	
## Locate argument in argv and return next item. Return empty string on error
# @param argv list of arguments
# @param argument argument that will be detected
# @pre argv is not empty list
# @pre argument is in argv
# @post returned string is not empty
def parse_arguments(argv, argument):
	i = 0
	for arg in argv:
		if arg == argument:
			if i+1 < len(argv):
				return argv[i+1]
			else:
				return None
		i += 1
	return None

## Prints error message with current date and time into file or into stderr
# @param arg message that will be printed
# @param file for output (None by default)
# @pre arg can be printed
# @pre err_file is already open wth mode that allows writing
def print_error(arg, err_file=None):
	current_time = "(" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ") "
	if err_file:
		err_file.write("collect.py: " + current_time + arg + "\n")
	else:
		sys.stderr.write("collect.py: " + current_time + arg + "\n")

################################################################################
argv = sys.argv

# detects --help argument
if "-h" in argv or "--help" in argv:
	print_help()
	exit(0)
	
err_file = None # variable for error output
err_file_name = None # filename of file for error output

# detects --errors argument
if "-e" in argv or "--errors" in argv:
	if "-e" in argv:
		err_file_name = parse_arguments(argv, "-e")
	else:
		err_file_name = parse_arguments(argv, "--errors")
	if not err_file_name:
		print_error("Could not detect error log file name", None)
		exit(1)
# if --errors argument is set, opens file for output
if err_file_name:
	try:
		err_file = open(err_file_name, 'w')
	except:
		print_error("Can't open error log file (" + err_file_name + ")", None)
		exit(0)

source = None # name of source file
url_src_file = None # variable for source file
# detect --input argument
if "-i" in argv or "--input" in argv:
	if "-i" in argv:
		source = parse_arguments(argv, "-i")
	else:
		source = parse_arguments(argv, "--input")
	if not source:
		print_error("Could not detect input file name", err_file)
		exit(1)
# if --input argument is set, open file, otherwise set file to stdin
if source:
	try:
		url_src_file = open(source, 'r')
	except:
		print_error("Can't open input file (" + source + ")", err_file)
		exit(1)
else:
	url_src_file = sys.stdin	


output = None # variable for storing filename of output file
# detecting --output argument
if "-o" in argv or "--output" in argv:
	if "-o" in argv:
		output = parse_arguments(argv, "-o")
	else:
		output = parse_arguments(argv, "--output")
	if not output:
		print_error("Could not detect output file name", err_file)
		exit(1)

append = False # if --append argument is not set, variable will not be changed
# detect --append argument, if set, change value of append variable as True
if "-a" or "--append" in argv:
	append = True

# if --output argument is set, open file, otherwise set stdout into output variable
if output:
	try:
		if append:
			output_file = open(output, 'a')
		else:
			output_file = open(output, 'w')
	except:
		print_error("Can't open output file (" + output + ")", err_file)
		exit(1)
else:
	output_file = sys.stdout

dedup_dir = None # name of directory for deduplication
dedup = [] # storing links for deduplication
# detect --dedup argument
if "-d" in argv or "--dedup" in argv:
	if "-d" in argv:
		dedup_dir = parse_arguments(argv, "-d")
	else:
		dedup_dir = parse_arguments(argv, "--dedup")
	if not dedup_dir:
		print_error("Invalid arguments", err_file)
		exit(1)
# if --dedup argument set, opens files in directory and store data
if dedup_dir:
	# setting / as last 'character' of string
	if dedup_dir[-1] != '/':
		dedup_dir += '/'
	try:
		files = os.listdir(dedup_dir) # list of filenames in directory
	except:
		print_error("Failed to load files in " + dedup_dir, err_file)
		exit(1)
	# load data from every file in directory and add them into dedup variable
	for filename in files:
		try:
			file = open(dedup_dir+filename, 'r')
			file_data = file.readlines()
			dedup += file_data
			file.close()
		except:
			print_error("Can't open file: " + filename, err_file)


url_src = url_src_file.readlines() # lines in source files
url_src_file.close() # closes source file

i = 0 # for indexing
# delete EOL and '/' if they are last characters
for url in url_src:
	while url[-1] == "/" or url[-1] == "\n":
		url = url[:-1]
		if not url:
			break
	url_src[i] = url
	i += 1

# delete duplicates
url_src = list(set(url_src))

links = [] # collected links (urls)
# collecting links
for rss in url_src:
	try:
		rss_page = urlopen(rss).read() # load data from page into variable
		root = ET.fromstring(rss_page) # preparing for processing data
		# items - list of tags (<tag></tag>) from page (not really sure what it is, but it works)
		items = [x for x in root.getchildren()[0].getchildren() if x.tag == "item"]
	except:
		print_error("Could not open url:" + rss, err_file)
		items = []

	# processing data from page
	if items:
		for item in items:
			try:
				url = item.find('link').text # retrieves link from item
				url = url.strip() + '\n'
				# check if link is not in files in dedup folder
				if len(url) > 0 and url not in dedup and url not in links:
					output_file.write(url)	
					links.append(url)
			except:
				pass #TODO AttributeError: 'NoneType' object has no attribute 'text' - line 203
