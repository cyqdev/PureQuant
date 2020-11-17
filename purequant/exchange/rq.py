from purequant.config import config
import requests


proxies = {
    'http': 'http://' + config.proxy,
    'https': 'https://' + config.proxy
}


def rq(method, url, **kwargs):
    return requests.request(method, url, proxies=proxies, **kwargs)


def get(url, params=None, **kwargs):
    return requests.get(url, params=None, proxies=proxies, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return requests.post(url, data=None, json=None, proxies=proxies, **kwargs)


def delete(url, **kwargs):
    return requests.delete(url, **kwargs)