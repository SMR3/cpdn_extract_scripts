#!/usr/bin/env python

###############################################################################
# Program : wah_extract_local.py
# Author  : Peter Uhe, based on original scripts by Neil Massey
# Date	  : 09/09/16
# Purpose : Script to specify the folder containing w@h zip files and extract the data of 
#           requested fields into separate netCDF files
###############################################################################

import sys, os
import ast
import tempfile, shutil
import glob
import argparse

from wah_extract_functions import extract_local,process_netcdf

###############################################################################

if __name__ == "__main__":
	urls_file = ""
	fields = ""
	output_dir = ""
	
	parser=argparse.ArgumentParser('Batch Extract Script:')
	in_dir_help='Input directory e.g. /gpfs/projects/cpdn/storage/boinc/upload/batch_440/successful/'
	parser.add_argument('-i','--in_dir',required=True,help=in_dir_help)
	out_dir_help='Base of output directory for extracted files(subdirectories for batch will be created)'
	parser.add_argument('-o','--out_dir',required=True,help=out_dir_help)
	
	fields_help='List of fields to extract: fields has the format:'
	fields_help+='\n      : [file_stream,stash_code,[region],process,valid_min,valid_max,time_freq,cell_method,vert_lev]'
	fields_help+='\n      : where file_stream = ga.pd|ga.pe|ma.pc'
	fields_help+='\n      :       stash_code = stash_section*1000 + stash_item'
	fields_help+='\n      :       [region] = [lon_l,lat_l,lon_r,lat_r]'
	fields_help+='\n      :        process = time post_processing: min|max|mean|sum|all'
	fields_help+='\n      :        time_freq = input variable data frequency in hours (e.g. 24=daily, 720=monthly)'
	fields_help+='\n      :        cell_method = input variable time cell method: minimum,maximum,mean'
	fields_help+='\n      :        vert_lev = (optional) input variable name of vertical level in netcdf file'
	parser.add_argument('-f','--fields',required=True,help=fields_help)

	parser.add_argument('-s','--start_zip',type=int,default=1,help='First zip to extract')
	parser.add_argument('-e','--end_zip',type=int,default=12,help='Last zip to extract')

	# Get arguments
	args = parser.parse_args()
	fields=args.fields
	output_dir=args.out_dir
	in_dir=args.in_dir
	start_zip=args.start_zip
	end_zip=args.end_zip
		
	# split the field list up
	field_list = ast.literal_eval(fields)
	for field in field_list:
		if len(field) != 9:
			print "Error! Fields argument not formatted correctly"
			print field
			print fields_help
			exit()
	
	# Get all workunit folders within batch folder
	taskdirs= glob.glob(in_dir+'/*')

	print 'fields',field_list
	print 'Number of tasks:',len(taskdirs)
	
	# create a temporary directory - do we have permission?
	temp_dir = tempfile.mkdtemp(dir='/home/'+os.environ['USER'])
	try:
		# Loop over tasks
		for u in list(taskdirs):
			print u
			
			# Extract zip files into temporary directory
			base_path,all_netcdfs=extract_local(u, field_list, output_dir, temp_dir,start_zip,end_zip)
			if not all_netcdfs:
				continue #something is wrong with this zip or files already exist, continue 
		
			# Process fields into single netcdf files
			for field in field_list:
				netcdfs=all_netcdfs[field[0]] # List of netcdf files for stream in field (e.g. 'ga.pe')
	#			print netcdfs
				for nc_in_file in netcdfs:
					out_netcdf=process_netcdf(nc_in_file,base_path,field)
					if not out_netcdf:
						break
					print os.path.basename(out_netcdf)
				
			# Remove netcdf files to stop temp directory getting too big
			for nc_list in all_netcdfs.itervalues():
				for fname in nc_list:
					os.remove(fname)
	except Exception,e:
		print 'Error extracting netcdf files',e
		raise
	finally:
		# remove the temporary directory
		shutil.rmtree(temp_dir)