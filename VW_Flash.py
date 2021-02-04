import sys
import logging
import argparse
import time

import lib.simos_flash_utils as simos_flash_utils
import lib.constants as constants

#udsoncan.setup_logging(path.join(path.dirname(path.abspath(__file__)), 'logging.conf'))
#logger = logging.getLogger("VWFlash")
#logger.info("Started with configuration: " + str(block_files))


#Set up logging (instead of printing to stdout)
cliLogger = logging.getLogger()

#Set it to debug by default
cliLogger.setLevel(logging.DEBUG)

#Set up a logging handler to print to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

#Set the logging format, and add the handler to the logger
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
cliLogger.addHandler(handler)

block_number_help = []
for name, number in constants.block_name_to_int.items():
    block_number_help.append(name)
    block_number_help.append(str(number))


#Set up the argument/parser with run options
parser = argparse.ArgumentParser(description='VW_Flash CLI', 
    epilog="The MAIN CLI interface for using the tools herein")
parser.add_argument('--action', help="The action you want to take", 
    choices=['checksum', 'checksum_fix', 'lzss', 'encrypt', 'prepare', 'flash_bin', 'flash_prepared'], required=True)
parser.add_argument('--infile',help="the absolute path of an inputfile", action="append")
parser.add_argument('--outfile',help="the absolutepath of a file to output", action="store_true")
parser.add_argument('--block', type=str, help="The block name or number", 
    choices=block_number_help, action="append", required=True)
parser.add_argument('--simos12', help="specify simos12, available for checksumming", action='store_true')

args = parser.parse_args()

def read_from_file(infile = None):
    f = open(infile, "rb")
    return f.read()

def write_to_file(outfile = None, data_binary = None):
    if outfile and data_binary:
        with open(outfile, 'wb') as fullDataFile:
            fullDataFile.write(data_binary)

if len(args.block) != len(args.infile):
    cliLogger.critical("You must specify a block for every infile")
    exit()

#convert --blocks on the command line into a list of ints
if args.block:
    blocks = [int(constants.block_to_number(block)) for block in args.block]

#build the dict that's used to proces the blocks
#  Everything is structured based on the following format:
#  {'infile1': {'blocknum': num, 'binary_data': binary},
#     'infile2: {'blocknum': num2, 'binary_data': binary2}
#  }
if args.infile:
    blocks_infile = {}
    for i in range(0, len(args.infile)):
        blocks_infile[args.infile[i]] = {'blocknum': blocks[i], 'binary_data': read_from_file(args.infile[i])}

else:
    print("No input file specified")
    exit()


#if statements for the various cli actions
if args.action == "checksum":
    simos_flash_utils.checksum(blocks_infile)

elif args.action == "checksum_fix":
    blocks_infile = simos_flash_utils.checksum_fix(blocks_infile)          

    if args.outfile:
        for filename in blocks_infile:
            binary_data = blocks_infile[filename]['binary_data']
            blocknum = blocks_infile[filename]['blocknum']
 
            write_to_file(data_binary = blocks_infile[filename]['binary_data'], outfile = filename.rstrip(".bin") + ".checksummed_block" + str(blocknum) + ".bin")
    else:
        cliLogger.critical("Outfile not specified, files not saved!!")


elif args.action == "lzss":
    simos_flash_utils.lzss_compress(blocks_infile, args.outfile)



elif args.action == "encrypt":
    blocks_infile = simos_flash_utils.encrypt_blocks(blocks_infile)

    if args.outfile:
        for filename in blocks_infile:
            binary_data = blocks_infile[filename]['binary_data']
            blocknum = blocks_infile[filename]['blocknum']
     
    
            outfile = filename + ".flashable_block" + str(blocknum)
            cliLogger.critical("Writing encrypted file to: " + outfile)
            write_to_file(outfile = outfile, data_binary = binary_data)
    else:
        cliLogger.critical("No outfile specified, skipping")


elif args.action == 'prepare':
    simos_flash_utils.prepareBlocks(blocks_infile)

elif args.action == 'flash_bin':
    cliLogger.critical("Executing flash_bin with the following blocks:\n" + 
      "\n".join([' : '.join([
           filename, 
           str(blocks_infile[filename]['blocknum']), 
           str(blocks_infile[filename]['binary_data'][constants.software_version_location[blocks_infile[filename]['blocknum']][0]:constants.software_version_location[blocks_infile[filename]['blocknum']][1]])]) for filename in blocks_infile]))


    simos_flash_utils.flash_bin(blocks_infile)

elif args.action == 'flash_prepared':
    simos_flash_utils.flash_prepared(blocks_infile)
