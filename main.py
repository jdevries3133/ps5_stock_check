"""
Script that continuously checks for PS5 inventory at the retailers below
and sends a message through a discord web hook when one is found.

This checks for the digital edition only because that is what I am looking
for. It can probably be tweaked to look for whatever edition you are looking
for by simply changing the url constants in the CheckStock class.
"""

import json
import time
import logging
from typing import List, NamedTuple
from pathlib import Path
import sys

import requests
from bs4 import BeautifulSoup


                        ### SETUP LOGGING ###
logging.basicConfig(
    filename=Path(Path(__file__).parent, 'stock_check.log')
)
logger = logging.getLogger(__name__)


                        ### SETUP CONFIG ###
with open(Path(Path(__file__).parent, 'config.json'), 'r') as jsonf:
    WEBHOOK_URL = json.load(jsonf)['WEBHOOK_URL']


def send_webhook_message(message: str) -> requests.models.Response:
    return requests.post(
        WEBHOOK_URL,
        json={
            'content': message
        },
        headers={'Content-Type': 'application/json'},
    )


class Result:
    def __init__(self, is_available: bool, message: str='', url: str=''):
        self.is_available = is_available
        self.message = message
        self.url = url


class CheckStock:

    # seconds to wait between checking
    TIME_SLEEP = 60

    PS5_URL_WALMART = (
        'https://www.walmart.com/ip/Sony-PlayStation-5-Digital-Edition'
        '/493824815?irgwc=1&sourceid=imp_VmuU&irgwc=1'
        '&sourceid=imp_0pfWoyR8ExyLTdlwUx0Mo37nUkES%3AmzJu3fh0Y0&veh=aff'
        '&wmlspartner=imp_1943169&clickid=0pfWoyR8ExyLTdlwUx0Mo37nUkES%3AmzJu3fh0Y0'
        '&sharedid=&affiliates_ad_id=565706&campaign_id=9383'
    )

    PS5_URL_SONY = (
        'https://direct.playstation.com/en-us/consoles/console'
        '/playstation5-digital-edition-console.3005817'
    )

    # link to visit to buy
    PS5_URL_BESTBUY_LISTING = (
        'https://www.bestbuy.com/site/playstation-5/playstation-5-packages'
        '/pcmcat1588107358954.c?irclickid=0ZXVqYR8ExyLThsxTSQPxVT4UkES%3Amwxu3fh0Y0'
        '&irgwc=1&ref=198&loc=Narrativ&acampID=0&mpid=376373'
    )

    # super weird html injection shenanigans going on... gotta go here to
    # get stock status ultimately
    PS5_URL_BESTBUY_CHECKSTOCK = (
        'https://www.bestbuy.com/site/canopy/component/fulfillment'
        '/add-to-cart-button/v1?addAllButtonSkus=&blockLevel=true&context=CLP'
        '&destinationZipCode=%24(csi.location.destinationZipCode)'
        '&deviceClass=%24(csi.deviceClass)&disableAttachModal=true'
        '&enableAddedToCartMessage=true&location=CLP&size=medium&skuId=6430161'
        '&storeId=%24(csi.location.storeId)'
    )

    def __init__(self):
        self._refresh_session()

    def __call__(self) -> List[Result]:
        """
        Calls all check_* functions and returns their results.
        """
        results = []
        for item in dir(self):
            if item.startswith('check_') and callable(getattr(self, item)):
                self._refresh_session()
                results.append(getattr(self, item)())
                time.sleep(self.TIME_SLEEP)

        return results

    def check_walmart(self):
        res = self.session.get(self.PS5_URL_WALMART)
        soup = BeautifulSoup(res.text, features='lxml')
        tag = soup.find('script', {'id': 'item'})
        try:
            jsn = json.loads(tag.contents[0])
        except TypeError:
            logging.exception(f'json could not be parsed: {tag}')
            return Result(is_available=False)
        try:
            status = jsn['item']['product']['buyBox']['products'][0]['availabilityStatus']
            return Result(
                is_available=status != 'OUT_OF_STOCK',
                message='PS5 is available at Walmart!',
                url=self.PS5_URL_WALMART
            )
        except KeyError:
            logging.exception('status not found')
            return Result(is_available=False)

    def check_sony(self):
        """
        For some reason, sony doesn't like the user agent spoofing, but is ok
        with python request's default user agent
        """
        res = requests.get(self.PS5_URL_SONY)
        soup = BeautifulSoup(res.text, features='lxml')
        status = soup.find(
            'div', {'class': 'productHero-mobile-price'}
        ).find('p').getText()
        if status == 'Out of Stock':
            return Result(is_available=False)
        return Result(
            is_available=True,
            message='PS5 is available from Sony!',
            url=self.PS5_URL_SONY
        )

    def check_bestbuy(self):
        res = self.session.get(self.PS5_URL_BESTBUY_CHECKSTOCK)
        soup = BeautifulSoup(res.text, features='lxml')
        status = soup.find('button', {'class': 'add-to-cart-button'}).getText()
        if status == 'Sold Out':
            return Result(is_available=False)
        return Result(
            is_available=True,
            message='PS5 is available at Best Buy!',
            url=self.PS5_URL_BESTBUY_LISTING
        )

    def _refresh_session(self):
        if hasattr(self, 'session'):
            self.session.close()
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent': (
                'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 '
                'Mobile Safari/537.36'
            )
        })

if __name__ == '__main__':
    while True:
        checker = CheckStock()
        try:
            results = checker()
            for r in results:
                if r.is_available:
                    send_webhook_message(
                        f'{r.message}\n\n{r.url}'
                    )
        except KeyboardInterrupt:
            sys.exit()

        except Exception:
            logger.exception('exception in main loop')
