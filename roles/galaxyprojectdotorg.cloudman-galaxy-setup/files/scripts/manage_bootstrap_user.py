#!/usr/bin/env python

import ConfigParser
import logging
import os
import re
import sys

import argparse

new_path = [ os.path.join( os.getcwd(), "lib" ) ]
new_path.extend( sys.path[1:] )
sys.path = new_path

from galaxy import eggs
eggs.require( "SQLAlchemy >= 0.4" )
eggs.require( 'mercurial' )

import galaxy.config
from galaxy.web import security
from galaxy.model import mapping

log = logging.getLogger( __name__ )


VALID_PUBLICNAME_RE = re.compile( "^[a-z0-9\-]+$" )
VALID_EMAIL_RE = re.compile( "[^@]+@[^@]+\.[^@]+" )


class BootstrapGalaxyApplication( object ):
    """
    Creates a basic Tool Shed application in order to discover the database
    connection and use SQL to create a user and API key.
    """

    def __init__( self, config ):
        self.config = config
        if not self.config.database_connection:
            self.config.database_connection = "sqlite:///%s?isolation_level=IMMEDIATE" % str( config.database )
        # Setup the database engine and ORM
        self.model = mapping.init( self.config.file_path,
                                   self.config.database_connection,
                                   engine_options={},
                                   create_tables=False )
        self.security = security.SecurityHelper( id_secret=self.config.id_secret )

    @property
    def sa_session( self ):
        """Returns a SQLAlchemy session."""
        return self.model.context.current

    def shutdown( self ):
        pass


def create_api_key( app, user ):
    api_key = app.security.get_new_guid()
    new_key = app.model.APIKeys()
    new_key.user_id = user.id
    new_key.key = api_key
    app.sa_session.add( new_key )
    app.sa_session.flush()
    return api_key


def get_or_create_api_key( app, user ):
    if user.api_keys:
        key = user.api_keys[0].key
    else:
        key = create_api_key( app, user )
    return key


def create_user( app, email, password, username ):
    if email and password and username:
        invalid_message = validate( email, password, username )
        if invalid_message:
            log.error(invalid_message)
        else:
            user = app.model.User( email=email )
            user.set_password_cleartext( password )
            user.username = username
            app.sa_session.add( user )
            app.sa_session.flush()
            app.model.security_agent.create_private_user_role( user )
            return user
    else:
        log.error("Missing required values for email: {0}, password: {1}, "
                  "username: {2}".format(email, password, username))
    return None


def get_or_create_user( app, email, password, username ):
    user = app.sa_session.query( app.model.User ).filter(
        app.model.User.table.c.username==username ).first()
    if user:
        return user
    else:
        return create_user( app, email, password, username )


def delete_user( app, username ):
    user = app.sa_session.query( app.model.User ).filter(
        app.model.User.table.c.username==username ).first()
    app.sa_session.delete( user )
    app.sa_session.flush()
    return user


def validate( email, password, username ):
    message = validate_email( email )
    if not message:
        message = validate_password( password )
    if not message:
        message = validate_publicname( username )
    return message


def validate_email( email ):
    """Validates the email format."""
    message = ''
    if not( VALID_EMAIL_RE.match( email ) ):
        message = "Please enter a real email address."
    elif len( email ) > 255:
        message = "Email address exceeds maximum allowable length."
    return message


def validate_password( password ):
    if len( password ) < 6:
        return "Use a password of at least 6 characters"
    return ''


def validate_publicname( username ):
    """Validates the public username."""
    if len( username ) < 3:
        return "Public name must be at least 3 characters in length"
    if len( username ) > 255:
        return "Public name cannot be more than 255 characters in length"
    if not( VALID_PUBLICNAME_RE.match( username ) ):
        return "Public name must contain only lower-case letters, numbers and '-'"
    return ''


def get_bootstrap_app(ini_file):
    config_parser = ConfigParser.ConfigParser( { 'here': os.getcwd() } )
    config_parser.read( ini_file )
    config_dict = {}
    for key, value in config_parser.items( "app:main" ):
        config_dict[ key ] = value
    config = galaxy.config.Configuration( **config_dict )
    app = BootstrapGalaxyApplication( config )
    return app


def create_bootstrap_user(ini_file, username, user_email, password):
    app = get_bootstrap_app(ini_file)
    user = get_or_create_user( app, user_email, password, username )
    if user is not None:
        api_key = get_or_create_api_key( app, user )
        print api_key
        exit(0)
    else:
        log.error("Problem creating a new user: {0} and an associated API key."
                  .format(username))
        exit(1)


def delete_bootstrap_user(ini_file, username):
    app = get_bootstrap_app(ini_file)
    user = delete_user( app, username )
    if user is not None:
        exit(0)
    else:
        log.error("Problem deleting user: {0}".format(username))
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="usage: python %prog [options]")
    parser.add_argument("-c", "--config",
                        required=True,
                        help="Path to <galaxy .ini file>")

    subparsers = parser.add_subparsers(title="action", help='create or delete bootstrap users')

    parser_create = subparsers.add_parser('create', help='create a new bootstrap user')
    parser_create.set_defaults(action='create')
    parser_create.add_argument("-u", "--username",
                        default="cloud",
                        help="Username to create. Defaults to 'cloud'",)
    parser_create.add_argument("-e", "--email",
                        default="cloud@galaxyproject.org",
                        help="Email for user",)
    parser_create.add_argument("-p", "--password",
                        default="password",
                        help="Password for user",)

    parser_delete = subparsers.add_parser('delete', help='delete an existing bootstrap user')
    parser_delete.set_defaults(action='delete')
    parser_delete.add_argument("-u", "--username",
                        default="cloud",
                        help="Username to delete. Defaults to 'cloud'",)
    args = parser.parse_args()

    if args.action == "create":
        create_bootstrap_user(args.config, args.username, args.email, args.password)
    elif args.action == "delete":
        delete_bootstrap_user(args.config, args.username)
