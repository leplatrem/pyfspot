import sys
import logging
import codecs 
import locale 
from optparse import OptionParser, OptionGroup
from gettext import gettext as _

from controller import FSpotController

logger = logging.getLogger(__name__)


def main(args=None):
    # Parse command-line arguments
    parser = OptionParser()
    parser.add_option("--database",
                      dest="database", default=None,
                      help=_("Path to F-Spot database"))
    parser.add_option("--log-level",
                      dest="log_level", default=logging.INFO, type='int',
                      help=_("Logging level for messages (1:debug 2:info, 3:warning, 4:errors, 5:critical)"))
    # Find
    lookupgrp = OptionGroup(parser, _("Queries"))
    lookupgrp.add_option("--find-path",
                      dest="find_path", default=None,
                      help=_("Find by path"))
    lookupgrp.add_option("--find-tag",
                      dest="find_tag", default=None,
                      help=_("Find by tag"))
    lookupgrp.add_option("--find-missing",
                      dest="find_missing", default=False, action="store_true",
                      help=_("Find photos missing on disk"))
    lookupgrp.add_option("--find-corrupted",
                      dest="find_corrupted", default=False, action="store_true",
                      help=_("Find corrupted Jpeg photos"))

    # Actions
    actionsgrp = OptionGroup(parser, _("Actions"))
    actionsgrp.add_option("--list",
                      dest="list", default=False, action="store_true",
                      help=_("List photos matching set"))
    actionsgrp.add_option("--rating",
                      dest="rating", default=None, type='int',
                      help=_("Change rating"))
    actionsgrp.add_option("--safe-rating",
                      dest="safe_rating", default=False, action="store_true",
                      help=_("Change rating only if superior to current"))
    actionsgrp.add_option("--tag",
                      dest="tag", default=None,
                      help=_("Apply specified tag"))
    actionsgrp.add_option("--untag",
                      dest="untag", default=None,
                      help=_("Remove specified tag"))
    parser.add_option_group(lookupgrp)
    parser.add_option_group(actionsgrp)
    (options, args) = parser.parse_args(args)
    
    logging.basicConfig(level = options.log_level)

    # Start using the controller
    fm = FSpotController(dbpath=options.database)
    logger.info(_("F-Spot version  : %s") % fm.fspot_version)
    logger.debug(_("F-Spot database : %s") % fm.db_version)

    # Chain find queries
    if options.find_path:
        path = unicode(options.find_path, 'utf8')
        fm.photoset = fm.find_by_path(path)
    if options.find_tag:
        tagname = unicode(options.find_tag, 'utf8')
        fm.photoset = fm.find_by_tag(tagname)
    if options.find_missing:
        fm.photoset = fm.find_missing_on_disk()
    if options.find_corrupted:
        fm.photoset = fm.find_corrupted()

    if options.rating:
        fm.change_rating(options.rating, options.safe_rating)
    if options.tag:
        fm.apply_tag(options.tag)
    if options.untag:
        fm.remove_tag(options.untag)

    # List photoset in stdout
    if options.list:
        # Force UTF-8 encoding of stdout
        #sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
        logger.debug(_("Default locale: %s") % locale.getdefaultlocale()[1])
        logger.debug(_("Terminal encoding (stdout): %s") % sys.stdout.encoding)
        for p in fm.photoset:
            print p.path

    if not any([options.list,
                options.rating,
                options.tag,
                options.untag]):
        logger.warning(_("No action was specified."))
    return 0

if __name__ == "__main__":
    code = main(sys.argv)
    sys.exit(code)
