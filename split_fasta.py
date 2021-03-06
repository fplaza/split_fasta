#!/usr/bin/env python

"""Split a multiFASTA file in several chunks"""

from __future__ import print_function
import argparse
import os
import sys
import math

__author__ = "Florian Plaza Onate, Amine Ghozlane"

def isfile(path):
    """Check if path is an existing file.
      Arguments:
          path: Path to the file
    """
    if not os.path.isfile(path):
        if os.path.isdir(path):
            msg = "{0} is a directory".format(path)
        else:
            msg = "{0} does not exist.".format(path)
        raise argparse.ArgumentTypeError(msg)
    return path


def isdir(path):
    """Check if path is an existing file.
      Arguments:
          path: Path to the file
    """
    if not os.path.isdir(path):
        if os.path.isfile(path):
            msg = "{0} is a file.".format(path)
        else:
            msg = "{0} does not exist.".format(path)
        raise argparse.ArgumentTypeError(msg)
    return path

def num_with_si_suffix(num):
    unit_to_value = {
            'k': 2**10,    # kilo
            'M': 2**20,    # mega
            'G': 2**30,    # giga
            'T': 2**40,   # tera
            }

    if num[-1].isdigit():
        value=float(num)
    else:
        value=float(num[0:-1])
        suffix=num[-1]
        if suffix not in unit_to_value.keys():
            msg = "unknown suffix '{0}'".format(suffix)
            raise argparse.ArgumentTypeError(msg)
        value *= unit_to_value[suffix]

    return int(value)

def get_parameters():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input-file', dest='fasta_file', required=True,
            default=argparse.SUPPRESS, type=isfile,
            help='Input FASTA file to split')
    parser.add_argument('-n', '--chunks', dest='num_chunks', type=int,
            help='Number of chunks')
    parser.add_argument('-m', '--max_file_size', dest='max_file_size',
            type=num_with_si_suffix, help='Instead of a precise number,'
            ' indicate an expected file size for each chunk in bytes'
            '(k, M, G, T suffixes are accepted).')
    parser.add_argument('-o', '--output-dir', dest='output_dir', type=isdir,
            default=os.curdir + os.sep, help='Output directory')
    return parser.parse_args(), parser


def read_fasta(fasta_stream):
    header, seq = None, []
    for line in fasta_stream:
        line = line.rstrip()
        if line.startswith(">"):
            if header:
                yield (header, ''.join(seq))
            header, seq = line, []
        else:
            seq.append(line)
    if header:
        yield (header, ''.join(seq))


def count_entries(fasta_file):
    count = 0
    try:
        with open(fasta_file, 'rt') as stream:
            for line in stream:
                if line.startswith(">"):
                    count += 1
    except IOError:
        sys.exit("Error cannot open {0}".format(fasta_file))
    return count


def split(fasta_file, chunk_size, output_dir):
    (fasta_file_basename,
            fasta_file_extension)  = os.path.splitext(os.path.basename(fasta_file))
    output_file_prefix = os.path.join(output_dir, fasta_file_basename)
    try:
        with open(fasta_file, 'rt') as stream:
            cur_chunk = 1
            entries_in_chunk = 0
            chunk_file = "{0}_{1}{2}".format(output_file_prefix, cur_chunk,
                    fasta_file_extension)
            chunk_stream = open(chunk_file, 'wt')
            for header, seq in read_fasta(stream):
                if (entries_in_chunk == chunk_size):
                    cur_chunk = cur_chunk + 1
                    entries_in_chunk = 0
                    chunk_stream.close()
                    chunk_file = "{0}_{1}{2}".format(output_file_prefix,
                            cur_chunk,
                            fasta_file_extension)
                    chunk_stream = open(chunk_file, 'wt')

                print("{1}{0}{2}".format(os.linesep, header, fill(seq)),
                        file=chunk_stream)
                entries_in_chunk = entries_in_chunk + 1
            chunk_stream.close()
    except IOError:
        sys.exit("Error cannot open {0}".format(fasta_file))

def fill(text, width=80):
    """Split text"""
    return os.linesep.join(text[i:i+width] for i in xrange(0, len(text), width))

def split_depending_on_size(fasta_file, max_file_size, output_dir):
    (fasta_file_basename,
            fasta_file_extension)  = os.path.splitext(os.path.basename(fasta_file))
    output_file_prefix = os.path.join(output_dir, fasta_file_basename)
    try:
        with open(fasta_file, 'rt') as stream:
            cur_chunk = 1
            file_size = 0
            chunk_file = "{0}_{1}{2}".format(output_file_prefix, cur_chunk,
                    fasta_file_extension)
            chunk_stream = open(chunk_file, 'wt')
            for header, seq in read_fasta(stream):
                if (file_size >= max_file_size):
                    cur_chunk = cur_chunk + 1
                    chunk_stream.close()
                    del(chunk_file)
                    file_size = 0
                    chunk_file = "{0}_{1}{2}".format(output_file_prefix,
                            cur_chunk,
                            fasta_file_extension)
                    chunk_stream = open(chunk_file, 'wt')

                output = "{1}{0}{2}{0}".format(os.linesep, header, fill(seq))
                chunk_stream.write(output)
                file_size += len(output)
            chunk_stream.close()
    except IOError:
        sys.exit("Error cannot open {0}".format(fasta_file))


if __name__ == '__main__':
    args, parser = get_parameters()
    if not args.num_chunks and not args.max_file_size:
        print("Please indicate the number of chunks or the max file size to "
                "split the fasta file !", file=sys.stderr)
        sys.exit(parser.print_help())

    if args.num_chunks:
        print("Start reading {0}".format(args.fasta_file))
        num_entries = count_entries(args.fasta_file)
        print("{0} has {1} FASTA entries".format(args.fasta_file, num_entries))
        chunk_size = (num_entries + args.num_chunks -1)/(args.num_chunks)
        print("Dividing {0} in {1} chunks of {2} entries".format(args.fasta_file,
            args.num_chunks,
            chunk_size))
        split(args.fasta_file, chunk_size, args.output_dir)
    elif args.max_file_size:
        print("Start creating chunks")
        split_depending_on_size(args.fasta_file, args.max_file_size,
                args.output_dir)
        print("Done")


