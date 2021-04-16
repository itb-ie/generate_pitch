import logging

logger = logging.getLogger("pitch_generator")
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

logger.info("This is a first test")