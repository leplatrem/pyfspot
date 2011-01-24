from controller import FSpotController

def main(args):
    fm = FSpotController()
    return 0

if __name__ == "__main__":
    logger.debug(_("Default terminal encoding: %s") % sys.getdefaultencoding())
    code = main(sys.argv)
    sys.exit(code)
