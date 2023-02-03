##  \package seal.app.resources
#   Global resources.


from seal.app.config import Config


#--  Resources  ----------------------------------------------------------------

##  The global resources include app, Config, Logger, and Server.

class Resources (object):

    ##  Constructor.

    def __init__ (self, app=None, config=None, log=None):
        if config is None:
            config = Config()
        if log is None:
            log = config.make_logger()

        ##  The application function.
        self.app = app

        ##  The configuration.
        self.config = config

        ##  The logger.
        self.log = log

        ##  The server.  This is added later.
        self.server = None

    def __str__ (self):
        return '<Resources app=%s config=%s>' % (self.app, self.config)
