import sys
import datetime
import pprint
from typing import Union, Dict, Tuple, List, Any
import logging
import enum


class ProxyTypeEnum(enum.Enum):
    UNKNOWN = 0
    STATIC = 1
    RESIDENTIAL = 2


class Proxy:

    def __init__(self, name="", totals=sys.maxsize, counter=0, last_update=datetime.datetime.now(), minutes_wait=5,
                 proxy_type=None, **kwargs):
        self.name = name
        self.totals = totals
        self.last_update = last_update
        self.counter = counter
        self.minutes_wait = minutes_wait
        self.proxy_type = proxy_type
        self._error_counter = 0
        self._is_used = False
        self._locked = False
        self._blocked = False

        self._update_state()

    def as_dict(self):
        return {
            "name": self.name,
            "totals": self.totals,
            "last_update": self.last_update,
            "counter": self.counter,
            "minutes_wait": self.minutes_wait
        }

    @property
    def mode(self):
        return self.proxy_type.value

    @property
    def remaining(self):
        return self.totals - self.counter

    def is_free(self):
        return not self._is_used and not self._locked

    def is_locked(self):
        return self._locked

    def is_available(self):
        return datetime.datetime.now() > self.last_update + datetime.timedelta(minutes=self.minutes_wait)

    def is_blocked(self):
        return self._blocked

    def calc_state(self):
        return (self.is_free() or self.is_free() and self.is_available()) and not self.is_blocked()

    def req_state(self):
        return (not self.is_locked() or self.is_available() and not self.is_locked()) and not self.is_blocked()

    def data(self):
        return {
            "https": self.name,
            "http": self.name
        }

    def _update_state(self):
        if self.counter < self.totals:
            self.last_update = datetime.datetime.now()
            self._locked = False
        else:
            self._locked = True

    def update_counter(self, value=1):
        self._is_used = True
        self.counter += value
        self._update_state()

    def reset_counter(self, value=0):
        self.counter = value
        self._is_used = False
        self._locked = False

    def update_error_counter(self, value=1):
        if self.proxy_type == ProxyTypeEnum.STATIC:
            self._error_counter += value
            self._blocked = True if self._error_counter > 2 else False

    def reset_error_counter(self):
        self._error_counter = 0

    def show(self):
        # return f"{self.name} - {self.counter} / {self.totals} [{self.req_state()}]"
        return f"{self.name} | State: {self.req_state()} | Used: [{100 * self.counter / float(self.totals):0.1f} %]"

    def __lt__(self, other):
        return self.remaining < other.remaining

    def __str__(self):
        return self.show()

    def __repr__(self):
        return self.show()


class ProxyManager:

    def __init__(self):
        self.lst_obj_proxy: List[Proxy] = []
        self._current_proxy = None
        self.name = str(self.__class__.__name__)
        self.logger = logging.getLogger(self.name)
        self._current_index = 0
        self.dict_indexes = {
            "static": 0,
            "residential": 0
        }


    def init_proxies(self, mode=0, lst_str_proxies=[]):

        if mode == ProxyTypeEnum.STATIC.value:
            # Read from utils
            for proxy_str_ in lst_str_proxies:
                self.add_proxy(Proxy(name=proxy_str_, proxy_type=ProxyTypeEnum.STATIC, minutes_wait=30,totals=1200))

        if mode == ProxyTypeEnum.RESIDENTIAL.value:
            # Read from utils
            for proxy_str_ in lst_str_proxies:
                self.add_proxy(Proxy(name=proxy_str_, proxy_type=ProxyTypeEnum.RESIDENTIAL, minutes_wait=30,totals=1200))

        self.logger.info(f"Init {len(self.lst_obj_proxy)} proxies")
        self._current_proxy = self.get_available_proxy()


    def gen_proxies_by_type(self, proxy_type=None):
        return [item_ for item_ in sorted(self.lst_obj_proxy, reverse=True) if item_.proxy_type == proxy_type]
        # return self.cycle_obj_proxies

    def get_available_proxy(self, mode=0) -> Union[Proxy, None]:
        lst_filtered_proxy = []
        key_index = ""

        if not mode:
            return None

        if mode == 1:
            lst_filtered_proxy = [item_ for item_ in self.gen_proxies_by_type(proxy_type=ProxyTypeEnum.STATIC) if
                                  item_.calc_state()]
            key_index = "static"
        elif mode == 2:
            lst_filtered_proxy = self.gen_proxies_by_type(proxy_type=ProxyTypeEnum.RESIDENTIAL)
            key_index = "residential"

        current_index = self.dict_indexes.get(key_index, 0)
        current_index += 1
        if current_index > len(lst_filtered_proxy) - 1:
            current_index = 0
        self.dict_indexes[key_index] = current_index

        return lst_filtered_proxy[current_index] if lst_filtered_proxy else None

    def update_current_available_proxy(self):
        self._current_proxy = self.get_available_proxy()
        self.logger.info(f"Change current proxy: {self._current_proxy}")

    def update(self):

        if isinstance(self._current_proxy, Proxy):
            self._current_proxy.update_error_counter()

            if self._current_proxy.is_blocked():
                self.update_current_available_proxy()

    def get_current_proxy(self):
        return self._current_proxy

    def add_proxy(self, data: Union[Dict, Proxy] = None, **kwargs):
        if not data and kwargs:
            data = kwargs

        if data:
            if isinstance(data, dict):
                self.lst_obj_proxy.append(Proxy(name=data.get("name", ""),
                                                totals=data.get("totals", 0),
                                                counter=data.get("counter", 0),
                                                last_update=data.get("last_update"),
                                                hours_wait=data.get("hours_wait", 24)))
            elif isinstance(data, Proxy):
                self.lst_obj_proxy.append(data)

    def find_by_name(self, name="") -> Proxy:
        return next((item_ for item_ in self.lst_obj_proxy if item_.name == name), None)

    def get_total_capacity(self):
        if self.lst_obj_proxy:
            return sum([item_.remaining for item_ in self.lst_obj_proxy])
        return 0

    def reset_all_proxies(self):

        for proxy_obj_ in self.lst_obj_proxy:
            proxy_obj_.reset_counter()
            proxy_obj_.reset_error_counter()

    def calculate_matrix(self, items: List[Dict] = []):

        dict_map = {}

        lst_available_proxy = sorted([item_ for item_ in self.lst_obj_proxy if item_.req_state()])

        for i in range(len(items)):
            item_ = items[i]
            target_proxy = lst_available_proxy[i % len(lst_available_proxy)] if lst_available_proxy else None

            if target_proxy:
                if target_proxy not in dict_map:
                    dict_map[target_proxy] = []
                dict_map[target_proxy].append(item_)

        return dict_map

    def calculate_matrix_old(self, items: Union[Dict[str, int], List[Tuple[str, int]], List[str]]):

        dict_map = {}
        index_ = 0

        dict_items = {}
        if isinstance(items, list):
            if items:
                if len(items[0]) == 2:
                    dict_items = {k: v for k, v in items}
                else:
                    dict_items = {k: 0 for k in items}

        elif isinstance(items, dict):
            dict_items = items

        lst_available_proxy = sorted([item_ for item_ in self.lst_obj_proxy if item_.req_state()])

        for item_ in dict_items:
            num_reqs_ = dict_items.get(item_, 0)
            proxy_best_fit = -sys.maxsize
            target_proxy = None

            if num_reqs_:

                for obj_proxy_ in lst_available_proxy:
                    value = obj_proxy_.remaining - (
                            sum([dict_items.get(el_, 0) for el_ in dict_map.get(obj_proxy_, [])]) + num_reqs_)

                    if proxy_best_fit < value:
                        proxy_best_fit = value
                        target_proxy = obj_proxy_
                        index_ = lst_available_proxy.index(obj_proxy_)
            else:
                target_proxy = lst_available_proxy[index_]
                index_ += 1
                index_ = 0 if index_ == len(lst_available_proxy) else index_

            if target_proxy:
                if target_proxy not in dict_map:
                    dict_map[target_proxy] = []
                dict_map[target_proxy].append(item_)

        return dict_map

    def show(self):
        return pprint.pformat(sorted(self.lst_obj_proxy))

    def __str__(self):
        return self.show()

    def __repr__(self):
        return self.show()


proxy_manager = ProxyManager()