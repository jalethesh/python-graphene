import logging

# lets go ahead and setup the system default logger as well
logging.basicConfig(filename='logs/default.log', filemode='a+', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)


def get_logger(name):
    fpath = f"logs/{name}.log"
    logger = logging.getLogger(name)
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    file_handler = logging.FileHandler(fpath)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def make_items_logger():
    fpath = f"logs/items.log"
    logger = logging.getLogger("items")
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    file_handler = logging.FileHandler(fpath)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def make_fuzzy_search_logger():
    fpath = f"logs/fuzzy_search.log"
    logger = logging.getLogger("items")
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    file_handler = logging.FileHandler(fpath)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def get_tests_logger():

    tests_log = logging.getLogger("tests")
    tests_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    tests_file_handler = logging.FileHandler('logs/tests.log')
    tests_file_handler.setFormatter(tests_formatter)
    tests_log.addHandler(tests_file_handler)
    return tests_log


def get_transactions_logger():
    tests_log = logging.getLogger("transactions")
    tests_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    tests_file_handler = logging.FileHandler('logs/transactions.log')
    tests_file_handler.setFormatter(tests_formatter)
    tests_log.addHandler(tests_file_handler)
    return tests_log



items_logger = make_items_logger()
fuzzy_search_logger = make_fuzzy_search_logger()
test_logger = get_tests_logger()
transaction_logger = get_transactions_logger()



# def celery_log_debug():
#     celery_log = get_celery_logger("celery")
#     print("testing celery logger")
#     celery_log.debug("simple celery logging test")
#
#
# def test_log_debug():
#     tests_log = get_tests_logger("tests")
#     print("testing logger")
#     tests_log.debug("basic logging test")