#!/usr/bin/env python
from __future__ import print_function
import atexit
import os
import shutil
import six
import sys
import tarfile
import tempfile

from . import version

try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    # Python 2.x compat
    from urllib2 import urlopen, HTTPError



CFG = dict(name='stak-notebooks',
           repo='https://github.com/spacetelescope',
           rev=version.__version__,
           ext='.tar.gz',
           tmpdir='',
           verbose=False)

def _unpack_archive(filename, destdir):
    '''Python 2.7 compat
    We prefer shutil.unpack_archive but this will have to do.
    '''
    with tarfile.open(filename, 'r:*') as tarball:
        tarball.extractall(destdir)


def download(url, destdir):
    bsize = 4096
    filename = os.path.join(destdir, os.path.basename(url))

    try:
        with open(filename, 'w+b') as ofp:
            data = urlopen(url)
            chunk = data.read(bsize)
            while chunk:
                ofp.write(chunk)
                chunk = data.read(bsize)
            data.close()
    except HTTPError as e:
        print('Requested invalid release version: {}\n(Developers, use "-l" for latest master)\n\nReason: {}\n'.format(version.__version__, e), file=sys.stderr)
        exit(1)

    return filename


@atexit.register
def cleanup():
    tmpdir = CFG['tmpdir']
    if tmpdir and os.path.exists(tmpdir):
        if CFG['verbose']:
            print('Removing {}'.format(tmpdir))
        shutil.rmtree(tmpdir)


def main():
    import argparse
    global CFG
    global verbose

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--latest', action='store_true', help='Ignore current release and download the latest available')
    parser.add_argument('-o', '--output-dir', action='store', type=str, default=os.curdir)
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing notebook directory')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    CFG['verbose'] = args.verbose

    # Pull from HEAD (only useful for active development)
    if args.latest:
        CFG['rev'] = 'master'

    # If the user issues an output directory, create the directory if it does not exist
    args.output_dir = os.path.abspath(args.output_dir)
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, mode=0o755)

    # Do not clobber existing notebooks if they exist
    expected = os.path.abspath(os.path.join(args.output_dir, '-'.join([CFG['name'], CFG['rev']])))
    if os.path.exists(expected) and not args.force:
        print('{} exists.\nUse --force to overwrite.'.format(expected), file=sys.stderr)
        exit(1)

    # Create temporary directory and store location in configuration
    CFG['tmpdir'] = tempfile.mkdtemp()

    # Compile URL
    url = '/'.join([CFG['repo'], CFG['name'], 'archive', CFG['rev'] + CFG['ext']])

    # Download archive to temp directory
    if CFG['verbose']:
        print('Retrieving {}'.format(url))
    archive = download(url, CFG['tmpdir'])

    # Extract archive in temp directory
    if CFG['verbose']:
        print('Unpacking {} to {}'.format(archive, args.output_dir))

    unpack_archive = _unpack_archive
    if six.PY3:
        unpack_archive = shutil.unpack_archive

    unpack_archive(archive, args.output_dir)
    # NOTE: cleanup() callback method deletes temporary directory


if __name__ == '__main__':
    main()
