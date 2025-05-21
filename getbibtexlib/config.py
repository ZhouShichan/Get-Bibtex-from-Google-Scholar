
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Union
from pathlib import Path
from omegaconf import OmegaConf
from loguru import logger


@dataclass
class Proxy:
    enable: bool = True
    host: str = "127.0.0.1"
    port: int = 7890


@dataclass
class BibtexRoute:
    url: str  # url with @@
    dom: str  # xpath
    keyword_regex: Optional[dict] = None  # 需要替换的正则表达式
    need_cookie: bool = False  # 是否需要cookie


@dataclass
class Headers:
    accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    accept_encoding: str = "gzip, deflate"
    accept_language: str = "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
    referer: str = ""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.36"
    # will be set with BibtexRoute in search_url_bases
    cookie: Optional[str] = ""

    def to_request_headers(self):
        headers = {
            "Accept": self.accept,
            "Accept-Encoding": self.accept_encoding,
            "Accept-Language": self.accept_language,
            "User-Agent": self.user_agent,
        }
        if self.referer:
            headers["Referer"] = self.referer
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers


@dataclass
class Config:
    headers: Headers = Headers()
    proxy: Proxy = Proxy()
    search_url_bases: Dict[str, BibtexRoute] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, adict: Dict):
        headers = Headers(**adict.get("header", {}))
        proxy = Proxy(**adict.get("proxy", {}))
        search_url_bases = {k: BibtexRoute(
            **v) for k, v in adict.get("search_url_bases", {}).items()}
        return cls(
            headers=headers,
            proxy=proxy,
            search_url_bases=search_url_bases,
            cookies=adict.get("cookies", {})
        )

    def to_dict(self):
        return {
            "header": asdict(self.headers),
            "proxy": asdict(self.proxy),
            "search_url_bases": {
                k: asdict(v) for k, v in self.search_url_bases.items()},
            "cookies": self.cookies.copy()
        }


DEFAULT_CONFIG = Config(
    headers=Headers(
        accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        accept_encoding="gzip, deflate",
        accept_language="zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        referer="",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36 Edg/100.0.1185.36",
    ),
    proxy=Proxy(
        enable=True,
        host="127.0.0.1",
        port=7890,
    ),
    search_url_bases={
        "dblp": BibtexRoute(
            url="https://dblp.org/search?q=@@",
            dom='//a[contains(@href, "?view=bibtex")]',
            keyword_regex={".html?view=bibtex": ".bib"},
            need_cookie=False,
        ),
        "google_scholar": BibtexRoute(
            url="https://scholar.google.com/scholar?q=@@/&output=cite",
            dom="//a[@class='gs_citi']",
            keyword_regex={},
            need_cookie=True,
        ),
    },
    cookies={}
)
