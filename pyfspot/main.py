import sys
import logging
import codecs 
import locale 
from optparse import OptionParser
from gettext import gettext as _

from controller import FSpotController

logger = logging.getLogger(__name__)

# Force UTF-8 encoding of stdout
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

def main(args):
    # Parse command-line arguments
    parser = OptionParser()
    parser.add_option("--database",
                      dest="database", default=None,
                      help=_("Path to F-Spot database"))
    parser.add_option("--find-path",
                      dest="find_path", default=None,
                      help=_("Find by path"))
    parser.add_option("--find-tag",
                      dest="find_tag", default=None,
                      help=_("Find by tag"))
    parser.add_option("--list",
                      dest="list", default=False, action="store_true",
                      help=_("List photos matching set"))
    parser.add_option("--log-level",
                      dest="log_level", default=logging.INFO, type='int',
                      help=_("Logging level for messages (1:debug 2:info, 3:warning, 4:errors, 5:critical)"))
    (options, args) = parser.parse_args(args)
    
    logging.basicConfig(level = options.log_level)

    # Start using the controller
    fm = FSpotController(dbpath=options.database)

    # Chain find queries
    if options.find_path:
        fm.photoset = fm.find_by_path(options.find_path)
    if options.find_tag:
        fm.photoset = fm.find_by_tag(options.find_tag)

    # List photoset in stdout
    if options.list:
        for p in fm.photoset:
            print p.path
    return 0

if __name__ == "__main__":
    code = main(sys.argv)
    sys.exit(code)
