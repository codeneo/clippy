import logging, redis
from time import sleep
from common import initialize_logger, get_clipboard, set_clipboard
from config import ApplicationConfig
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import InvalidToken
from multiprocessing import Process, Manager
from ctypes import c_wchar_p


logger = logging.getLogger('app')


def initialize_app(args):
    logger.info(f"Initializing ApplicationConfig from json file: [{args.config}]")
    application_config = ApplicationConfig.from_json(args.config)
    logger.debug(f"Initialized ApplicationConfig: [{application_config=}]")
    logger.debug(f"Initializing Redis session with config: [{application_config.redis=}]")
    redis_url = application_config.redis.remote_url if args.remote else application_config.redis.local_url
    redis_session = redis.from_url(url=redis_url, decode_responses=True)
    logger.debug(f"Initialized Redis session: [{redis_session=}]")
    if args.remote and not application_config.cipher.enabled:
        logger.warn("The remote Redis instance will be data aware. Please consider enabling encryption for sensitive data.")
    logger.info(f"Sending PING to Redis")
    response = redis_session.ping()
    logger.info(f"Response from Redis: [{response=}]")
    logger.debug(f"Initializing Cipher with config: [{application_config.cipher=}]")
    cipher = Fernet(application_config.cipher.key) if application_config.cipher.enabled else None
    logger.debug(f"Initialized Cipher: [{cipher=}]")
    return application_config, redis_session, cipher


def producer(redis_session, channel, cipher, shared, lock):
    value = ''
    while(True):
        is_updated, value = get_clipboard(last_seen=value)
        if is_updated:
            logger.debug(f"Clipboard changed to: [{value=}]")
            try:
                lock.acquire()
                if value != shared.value:
                    encrypted_value = cipher.encrypt(value.encode('utf-8')) if cipher else None
                    redis_session.publish('clippy', encrypted_value.decode('utf-8') if cipher else value)
                    logger.info(f"Message sent.")
            finally:
                lock.release()
        sleep(5)


def consumer(redis_session, channel, cipher, shared, lock):
    pubsub = redis_session.pubsub()
    pubsub.subscribe(channel)
    logger.info(f"Subscribed to channel: [{channel=}]")
    for message in pubsub.listen():
        logger.info(f"Message recieved:")
        logger.debug(f"{message=}")
        if message and isinstance(message, dict) and message.get('type') == 'message':
            data = message.get('data')
            logger.debug(f"Data: [{data=}]")
            try:
                data = cipher.decrypt(data.encode('utf-8')).decode('utf-8') if cipher else data
                if cipher: logger.debug(f"Decrypted Data: [{data=}]")
                lock.acquire()
                shared.value = data
                set_clipboard(value=data)
            except (InvalidSignature, InvalidToken) as e:
                logger.exception(f"Decryption failed for: [{data=}]")
            finally:
                lock.release()


def main(args):
    try:
        application_config, redis_session, cipher = initialize_app(args)
        manager = Manager()
        shared, lock = manager.Value(c_wchar_p, ''), manager.Lock()
        consumer_process = Process(target=consumer, args=(redis_session, application_config.redis.channel, cipher, shared, lock))
        producer_process = Process(target=producer, args=(redis_session, application_config.redis.channel, cipher, shared, lock))
        consumer_process.start(), producer_process.start()
        consumer_process.join(), producer_process.join()
    finally:
        logger.info(f"Closing connection(s) to Redis...")
        redis_session.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Clipboard sync client.')
    required_arguments, optional_arguments = parser.add_argument_group('required arguments'), parser.add_argument_group('optional arguments')
    optional_arguments.add_argument('--config',
                                    help='the config file location',
                                    type=str,
                                    action='store',
                                    dest='config',
                                    required=False,
                                    default='config.json')
    optional_arguments.add_argument('--remote',
                                    help='connect to remote instance',
                                    type=bool,
                                    action='store_true',
                                    dest='remote',
                                    required=False)
    optional_arguments.add_argument('--debug',
                                    help='enable debug',
                                    type=bool,
                                    action='store_true',
                                    dest='debug',
                                    required=False)
    args = parser.parse_args()
    initialize_logger(level=logging.DEBUG if args.debug else logging.INFO)
    main(args)

