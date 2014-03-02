#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup.py

from ConfigParser import ConfigParser
from grp import getgrnam
from pwd import getpwnam
from setuptools import setup
from distutils.sysconfig import get_python_lib
from sys import stderr, stdout, exit
import loris
import os
from loris.transforms import JP2_Transformer 
		
VERSION = loris.__version__

BIN_DP = '/usr/local/bin'
ETC_DP = '/etc/loris'
LIB_DP = '/usr/local/lib'

KDU_EXPAND_TARGET = os.path.join(BIN_DP, 'kdu_expand')
KDU_LIBS_TARGET = os.path.join(LIB_DP, JP2_Transformer.libkdu_name())
LORIS_CACHE_CLEAN = os.path.join(BIN_DP, 'loris-cache_clean.sh')

this_dp = os.path.abspath(os.path.dirname(__file__))

# Get the config file
conf_fp = os.path.join(this_dp, 'etc', 'loris.conf')
conf = ConfigParser()
conf.read(conf_fp)

# Make sure the ultimate owner of the app exists before we go any further
try:
	user_n = conf.get('loris.Loris', 'run_as_user')
	group_n = conf.get('loris.Loris', 'run_as_group')
	user = getpwnam(user_n)
	group = getgrnam(group_n)
	user_id = user.pw_uid
	group_id = group.gr_gid
except KeyError:
	msg = '''
User "%s" and or group "%s" do(es) not exist.
Please create this user, e.g.:
	`useradd -d /var/www/loris -s /sbin/false loris`

'''% (user_n,group_n)
	stderr.write(msg)
	exit(67)


cache_dp = conf.get('img.ImageCache', 'cache_dp')
cache_links = conf.get('img.ImageCache', 'cache_links')
info_cache_dp = conf.get('img_info.InfoCache', 'cache_dp')
www_dp = conf.get('loris.Loris', 'www_dp')
tmp_dp = conf.get('loris.Loris', 'tmp_dp')
log_dp = conf.get('logging', 'log_dir')

# If all of that worked, determine requirements
install_requires = []
try:
	import werkzeug
except ImportError:
	install_requires.append('werkzeug>=0.8.3')

data_files=[
	(ETC_DP, ['etc/loris.conf']),
	(BIN_DP, ['bin/loris-cache_clean.sh', 'bin/iiif_img_info', JP2_Transformer.local_kdu_expand_path()]),
	(LIB_DP, [JP2_Transformer.local_libkdu_path()]),
	(log_dp, []),
	(cache_dp, []),
	(cache_links, []),
	(info_cache_dp, []),
	(www_dp, ['www/loris.wsgi']),
	(www_dp, ['www/index.txt']),
	(tmp_dp, []),
]

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name='Loris',
	author='Jon Stroop',
	author_email='jstroop@princeton.edu',
	url='https://github.com/pulibrary/loris',
	description = ('IIIF Image API 1.1 Level 2 compliant Image Server'),
	long_description=read('README.md'),
	license='GPL',
	version=VERSION,
	packages=['loris'],
	install_requires=install_requires,
	data_files=data_files,
	test_suite = 'tests'
)

loris_owned_dirs = list(set([n[0] for n in data_files]))
loris_owned_dirs.remove(LIB_DP)
loris_owned_dirs.remove(BIN_DP)

# Change permissions for all the new dirs to Loris's owner.
for fs_node in loris_owned_dirs:
	os.chmod(fs_node, 0755)
	os.chown(fs_node, user_id, group_id)

wsgi_script = os.path.join(www_dp, 'loris.wsgi')
executables = (LORIS_CACHE_CLEAN, KDU_EXPAND_TARGET, wsgi_script)
for ex in executables:
	os.chmod(ex, 0755)
	os.chown(ex, user_id, group_id)

index = os.path.join(www_dp, 'index.txt')
os.chmod(index, 0644)
os.chown(index, user_id, group_id)

todo = '''
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
Installation was successful. Here's where things are:

 * Loris configuration: %(config)s
 * Cache cleaner cron: %(cache_clean)s
 * kdu_expand: %(kdu_expand)s
 * Kakadu libraries: %(libkdu)s
 * Logs: %(logs)s
 * Image cache (opaque): %(cache_dp)s
 * Image cache (symlinks that look like IIIF URIs): %(cache_links)s
 * Info cache: %(info_cache_dp)s
 * www/WSGI application directory: %(www_dp)s
 * Temporary directory: %(tmp_dp)s

However, you have more to do. See README.md and doc/deployment.md for details. 
In particular:

 0. You should have read README.md already, and know what I'm talking about.

 1. Make sure that the Python Imaging Library is installed and working. See 
	notes about this in doc/dependencies.md.

 2. Configure the cron job that manages the cache (bin/loris-cache_clean.sh, 
	now at %(cache_clean)s). Make sure the constants match 
	how you have Loris configured, and then set up the cron 
	(e.g. `crontab -e -u %(user_n)s`).

 3. Have a look at the WSGI file in %(www_dp)s. It should be fine as-is, but 
	there's always a chance that it isn't. The first thing to try is explictly
	adding the package to your PYTHONPATH (see commented code).

 4. Configure Apache (see doc/apache.md).

You may want to save this message as the path information above is the most 
comprehensive information about what this script just did, what's installed 
where, etc.

Cheers! -Js
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
''' % {
	'cache_clean' : LORIS_CACHE_CLEAN,
	'cache_dp' : cache_dp,
	'cache_links' : cache_links,
	'config' : ETC_DP,
	'info_cache_dp' : info_cache_dp,
	'kdu_expand' : KDU_EXPAND_TARGET,
	'libkdu' : KDU_LIBS_TARGET,
	'logs' : log_dp,
	'tmp_dp' : tmp_dp,
	'user_n' : user_n,
	'www_dp' : www_dp
}

stdout.write(todo)
