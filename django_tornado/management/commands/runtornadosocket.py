from os import path as op
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option

import os
import sys
import tornado.web
import tornadio
import tornadio.router
import tornadio.server

ROOT = op.normpath(op.dirname(__file__))
        
from chatroom.view import ChatRouter

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--reload', action='store_true',
            dest='use_reloader', default=False,
            help="Tells Tornado to use auto-reloader."),
        make_option('--flash_policy_file', action='store_true',
            dest='flash_policy_file', default=False,
            help="Location of 'flash_policy_file' "),
        #make_option('--adminmedia', dest='admin_media_path', default='',
        #    help="Specifies the directory from which to serve admin media."),
        make_option('--noxheaders', action='store_false',
            dest='xheaders', default=True,
            help="Tells Tornado to NOT override remote IP with X-Real-IP."),
        
    )
    help = "Starts a Tornado Web Socket Server."
    args = '[optional port number or ipaddr:port] (one or more, will start multiple servers)'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False
 
    def handle(self, *addrport, **options):
        # reopen stdout/stderr file descriptor with write mode
        # and 0 as the buffer size (unbuffered).
        # XXX: why?
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)
 
        if len(addrport) == 0 :
            raise CommandError('Usage is runserver %s' % self.args)

        if len(addrport) == 1 :
            self.run_one(addrport[0], **options)
        else :
            from multiprocessing import Process

            plist = []
            for ap in addrport :
                p = Process(target=self.run_one, args=(ap,), kwargs=options)
                p.start()
                plist.append(p)

            # for p in plist : plist.terminate()

            while plist :
                if plist[0].exitcode is None :
                    plist.pop(0)
                else :
                    plist[0].join()
            

    def run_one(self, addrport, **options) :
        import django
        from django.core.handlers.wsgi import WSGIHandler
        from tornado import httpserver, wsgi, ioloop, web

        if not addrport:
            addr = ''
            port = '8888'
        else:
            try:
                addr, port = addrport.split(':')
            except ValueError:
                addr, port = '', addrport
        if not addr:
            addr = '127.0.0.1'
 
        if not port.isdigit():
            raise CommandError("%r is not a valid port number." % port)
 
        use_reloader = options.get('use_reloader', False)

        flash_policy_file = options.get(
            'flash_policy_file',  
            getattr(settings, "FLASH_POLICY_FILE", op.join(ROOT, 'flashpolicy.xml'))
        )

        xheaders = options.get('xheaders', True)

        shutdown_message = options.get('shutdown_message', '')
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        if settings.DEBUG :
            import logging
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)
 
        def inner_run():
            from django.conf import settings
            from django.utils import translation
            print "Validating models..."
            self.validate(display_num_errors=True)
            print "\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE)
            print "Socket Server is running at http://%s:%s/" % (addr, port)
            print "Quit the server with %s." % quit_command

            # django.core.management.base forces the locate to en-us. We
            # should set it up correctly for the first request
            # (particularly important in the not "--reload" case).
            translation.activate(settings.LANGUAGE_CODE)
            
            try:
                # Instance Django's wsgi handler.
                application = web.Application(
                    [ ChatRouter.route()],
                    enabled_protocols = ['websocket',
                                        'flashsocket',
                                        'xhr-multipart',
                                        'xhr-polling'],
                    flash_policy_port = 8843,
                    flash_policy_file = flash_policy_file,
                    socket_io_port = port
                )
                # start tornado web server in single-threaded mode
                # instead auto pre-fork mode with bind/start.
                tornadio.server.SocketServer(application)

            except KeyboardInterrupt:
                if shutdown_message:
                    print shutdown_message
                sys.exit(0)
 
        if use_reloader:
            # Use tornado reload to handle IOLoop restarting.
            from tornado import autoreload
            autoreload.start()

        inner_run()


