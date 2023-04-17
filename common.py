import logging, pyperclip, sys
from time import sleep


logger = logging.getLogger('common')


def initialize_logger(level):
    logging.basicConfig(stream=sys.stdout, level=level, datefmt="%Y-%m-%d %H:%M:%S",
                        format='%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s')


def get_clipboard(last_seen):
    value = str(pyperclip.paste())
    # print(f"{value=}, {last_seen=}")
    is_updated = value is not None and value != last_seen
    return is_updated, value if is_updated else last_seen


def set_clipboard(value):
    pyperclip.copy(value)


def main():
    # logger test
    initialize_logger(logging.DEBUG)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.error("This is an error message.")
    # get_clipboard test
    logger.info(f"Getting clipboard.")
    is_updated, value = get_clipboard(last_seen='')
    if is_updated: logger.info(f"Clipboard updated: [{value=}]")
    sleep(5)
    # set_clipboard test
    for value in ['Hello World!', ' ', '']:
        logger.info(f"Setting clipboard: [{value=}]")
        set_clipboard(value=value)
        # ctrl/cmd+v to verify the clipboard
        sleep(5)


if __name__ == '__main__':
    print(f"Executing submodule [{__file__}] as a script.")
    main()

