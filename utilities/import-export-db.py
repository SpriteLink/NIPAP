#!/usr/bin/python
""" Script for importing / exporting nipap db
    =========================================

    The script can export and import the nipap PostgreSQL database.

    Import
    ------
    During the import it does not check if the nipap db has the correct schema version.
    During the import, if the nipap config file exists at the specified location 
    (or at the default location '/etc/nipap/nipap.conf), the script will gather
    the db username and password from the config file (section 'nipapd')

    Arguments
    ^^^^^^^^^
    * '-if INFILE' - Input file (contains PostgreSQL db)
    * '-u USER' - Run psql commands as specified user (should be psql admin)
    * '-db DB' - Import the file in the specified database
    * '-du USER' - Make the specified user owner of the DB 
                  (the user will be created if it doesn't exist)
    * '-dp PASSWORD' - Use the specified password for the db user
                      (only required if the user doesn't exist)
    * '-nconf PATH' - Read the DB user and password ('-du', -dp') from the specified
                      NIPAP config file

    Export
    ------
    The specified user for exporting requires write permission to the export location.
    Additionally, the user needs to be able to authenticate with PostgreSQL.

    Arguments
    ^^^^^^^^^
    * '-of OUTFILE' - Export the database to the specified file
    * '-db DB' - Export the specified PostgreSQL database
    * '-u USER' - Run psql commands as specified user
"""

import os
import sys
import subprocess
import argparse

class Export:
    def write(self, args):
        """
        """
        if args.outfile is None:
            print >> sys.stderr, "Error: Please specify an output file for the export."
            sys.exit(1)

        if os.path.exists(args.outfile):
            print >> sys.stderr, "Error: Output file %s already exists. Please specify a different output file." % args.outfile
            sys.exit(1)

        print('Trying to export PostgreSQL database "%s" as user "%s"' % (args.database, args.user))
        ret = subprocess.call(['su', args.user, '-c', 'pg_dump ' + args.database + ' -f ' + args.outfile])

        if ret == 0:
            print('Database "%s" exported successfully to file %s' % (args.database, args.outfile))
        else:
            print('There was an error exporting the database "%s" to file %s' % (args.database, args.outfile))
            print('Make sure the user "%s" has write permission.' % args.user)

class Import:
    def read(self, args):
        """
        """
        if args.infile is None:
            print >> sys.stderr, "Error: Please specify an input file for the import."
            sys.exit(1)

        if os.path.exists(args.infile) is False:
            print >> sys.stderr, "Error: Input file %s does not exist. Please specify a different input file." % args.infile
            sys.exit(1)

        if os.path.exists(args.nconf) is True:
            from nipap.nipapconfig import NipapConfig
            cfg = NipapConfig(args.nconf)
            dbuser = cfg.get('nipapd', 'db_user')
            if dbuser in (None, '') is False:
                args.dbuser = dbuser
                args.dbpass = cfg.get('nipapd', 'db_pass')
                print('Using "%s" as DB user with password "%s" from config %s' % (args.dbuser, args.dbpass, args.nconf))

        FNULL = open(os.devnull, 'w')

        #check if the specified postgresql user already exists
        ret = subprocess.call(['su', args.user, '-c', 'psql postgres -tAc "SELECT 1 FROM pg_roles where rolname=\'' + args.dbuser + '\'" | grep 1'], stdout=FNULL)
        #if not, create the postgresql user
        if ret == 1:
            if args.dbpass is None:
                print >> sys.stderr, "Error: Please specify a DB password for the DB user \"%s\"" % args.dbuser
                sys.exit(1)

            subprocess.call(['su', args.user, '-c', 'createuser -S -D -R -w ' + args.dbuser])
            subprocess.call(['su', args.user, '-c', 'psql -q -c "ALTER USER ' + args.dbuser + ' ENCRYPTED PASSWORD \'' + args.dbpass + '\'"'])
            print('PostgreSQL DB user "%s" with password "%s" has been successfully created. Make sure to use these credentials in your nipap.conf.\n' % (args.dbuser, args.dbpass))

        #check if the specified postgres database exists
        _ret = subprocess.call(['su', args.user, '-c', 'psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname=\'' + args.database + '\'" | grep 1'], stdout=FNULL)
        if _ret == 1:
            subprocess.call(['su', args.user, '-c', 'createdb -O' + args.dbuser + ' ' + args.database])
        else:
            print('It seems the PostgreSQL database "%s" already exists. Make sure the PostgreSQL user "%s" is the owner of the database!\n' % (args.database, args.dbuser))
            answer = ''
            while (answer in ('Yes', 'No')) is False:
                print('Do you want to continue importing %s to the database %s? Answer with [Yes] or [No]' % (args.infile, args.database))
                answer = raw_input()

            if answer == 'No':
                sys.exit(1)

        subprocess.call(['su', args.user, '-c', 'createlang -d ' + args.database + ' plpgsql'], stdout=FNULL, stderr=FNULL)
        #do the actual import
        _ret = subprocess.call(['su', args.user, '-c', 'psql ' + args.database + ' < ' + args.infile], stdout=FNULL)
        if _ret == 0:
            print('Input file "%s" successfully imported to database "%s"' % (args.infile, args.database))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NIPAP Import / Export Tool')
    parser.add_argument('action', metavar='{import, export}', nargs='?', type=str, choices=['import', 'export'], help='define an action to execute')
    parser.add_argument('-u', '--user', dest='user', type=str, default='postgres', help='PostgreSQL User (default=postgres)')
    parser.add_argument('-db', '--database', dest='database', type=str, default='nipap', help='Database name (default=nipap)')
    parser.add_argument('-du', '--dbuser', dest='dbuser', type=str, default='nipap', help='DB username (default=nipap)')
    parser.add_argument('-dp', '--dbpass', dest='dbpass', type=str, help='Password for the DB user')
    parser.add_argument('-if', '--infile', dest='infile', type=str, help='Input file for import')
    parser.add_argument('-of', '--outfile', dest='outfile', type=str, help='Output file for export')
    parser.add_argument('-nconf', '--nipapconfig', dest='nconf', type=str, default='/etc/nipap/nipap.conf', help='NIPAP config file path')
    args = parser.parse_args()


    if os.geteuid() != 0:
        print >> sys.stderr, "Error: You need to be root to run this script."
        sys.exit(1)

    if args.action == 'export':
        print('\nNIPAP Import / [Export] Tool\n')
        ex = Export()
        ex.write(args)

    elif args.action == 'import':
        print('\nNIPAP [Import] / Export Tool\n')
        im = Import()
        im.read(args)

    else:
        parser.print_help()