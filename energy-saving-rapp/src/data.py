import time
import pandas as pd
import requests
from influxdb import DataFrameClient
from configparser import ConfigParser
import logging
from mdclogpy import Logger
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from requests.exceptions import RequestException, ConnectionError
import json
import os
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient, Point, WriteOptions


logger = Logger(name=__name__)


class DATABASE(object):
    
    def __init__(self, dbname='Timeseries', user='root', password='root', host="r4-influxdb.ricplt", port='8086', ssl=False):
        self.token = None
        self.org = None
        self.bucket = None
        self.data = None
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = ssl
        self.dbname = dbname
        self.client = None
        self.address = None
        self.config()

    def connect(self):
        if self.client is not None:
            self.client.close()

        try:
            self.client = influxdb_client.InfluxDBClient(url=self.address, org=self.org, token=self.token)
            version = self.client.version()
            logger.info("Connected to Influx Database, InfluxDB version : {}".format(version))
            return True

        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError):
            logger.error("Failed to establish a new connection with InflulxDB, Please check your url/hostname")
            time.sleep(120)

    def read_data(self, train=False, valid=False, limit=False):

        self.data = None
        query = 'from(bucket:"{}")'.format(self.bucket)
        query += '|> range(start: -8m) '
        query += ' |> filter(fn: (r) => r["_measurement"] == "o-ran-pm")'
        query += ' |> filter(fn: (r) => r["_field"] == "CellID" or r["_field"] == "RRC.ConnMean") '
        query += ' |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") '
        result = self.query(query)
        self.data = result
        return result

    def query(self, query):
        try:
            query_api = self.client.query_api()
            result = query_api.query_data_frame(org=self.org, query=query)
            logger.info(f'Cell data : {result}')
        except (RequestException, InfluxDBClientError, InfluxDBServerError, ConnectionError) as e:
            logger.error('Failed to connect to influxdb: {}'.format(e))
            result = False
        return result

    def config(self):
        cfg = ConfigParser()
        cfg.read('config.ini')
        for section in cfg.sections():
            if section == 'influxdb':
                self.host = cfg.get(section, "host")
                self.port = cfg.get(section, "port")
                self.user = cfg.get(section, "user")
                self.password = cfg.get(section, "password")
                self.ssl = cfg.get(section, "ssl")
                self.dbname = cfg.get(section, "database")
                self.meas = cfg.get(section, "measurement")
                self.token = cfg.get(section, "token")
                self.org = cfg.get(section, "org")
                self.bucket = cfg.get(section, "bucket")
                self.address = cfg.get(section, "address")

