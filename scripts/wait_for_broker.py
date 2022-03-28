#!/usr/bin/env python3
import os
import pika

def main():
    broker_url = os.environ.get('BROKER_URL')
    connection_param = pika.connection.URLParameters(broker_url)
    print('Checking broker connection...')
    connection = pika.BlockingConnection(connection_param)
    if connection.is_open:
        print('Connection is ready...')
        connection.close()

if __name__ == '__main__':
    main()
    exit(0)
