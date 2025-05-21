from loguru import logger
from lxml import etree
import bibtexparser as bp
import requests

from .config import Config, BibtexRoute


def convert_to_latex_compatible(s):
    """
    将字符串中的特殊字符转换为LaTeX兼容的形式。

    Args:
        s (str): 需要转换的字符串。

    Returns:
        str: 转换后的LaTeX兼容字符串。
    """
    latex_special_chars = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    for char, latex in latex_special_chars.items():
        s = s.replace(char, latex)
    return s


def format_bibtex(bibtex_str):
    # Parse the BibTeX string
    bib_database = bp.loads(bibtex_str)
    res = []
    for entry in bib_database.entries:
        # 对每个字段应用转换并去除多余空白字符
        max_length = 0
        entry_value_dict = {}
        for key in sorted(entry.keys()):
            if key in ["ENTRYTYPE", "ID"]:
                continue
            original_value = entry[key]
            # 去除多余的换行符和制表符
            cleaned_value = original_value.replace("\n", " ").replace("\t", " ").strip()
            # 转换成LaTeX兼容格式
            entry_value_dict[key] = convert_to_latex_compatible(cleaned_value)
            max_length = max(max_length, len(key))
        # 右对齐 key
        tmp = [
            f"@{entry['ENTRYTYPE']}{{{entry['ID']},",
            *[
                f"  {key.ljust(max_length)}    = {{{value}}},"
                for key, value in entry_value_dict.items()
            ],
            f"}}",
        ]
        res.append("\n".join(tmp))
    return "\n\n".join(res)


def get_bibtex_common(config: Config, query: str, source="google_scholar"):
    if source not in config.search_url_bases:
        logger.error(
            "Source {} is not supported, please use one of {}.".format(
                source, Config.search_url_bases.keys()
            )
        )
        return None

    # 暂时只支持单页面跳转的检索模式, 也就是只有一个bibtex_route
    source_settings: BibtexRoute = config.search_url_bases[source]
    url = source_settings.url
    search_url = url.replace("@@", query)
    need_cookie = source_settings.need_cookie

    headers: dict = config.headers.to_request_headers()  # type: ignore
    headers["Referer"] = search_url.split("?")[0]
    headers["Cookie"] = config.cookies.get(source, "")
    if need_cookie and not headers["Cookie"]:
        logger.error(
            "No cookie for {}! Please visit this page {} to get your cookie.".format(
                source, url.replace("@@", "1")
            )
        )
        return None
    # get the first article id
    try:
        res = requests.get(search_url, headers=headers)
    except Exception as e:
        logger.error(f"Error occur when fetching {search_url}: {e}")
        return None
    content = res.text
    html = etree.HTML(content, parser=etree.HTMLParser(encoding="utf-8"))
    dom_xpath = source_settings.dom
    elements = html.xpath(dom_xpath)
    if elements == []:
        logger.error(f"{query} not found in {source}.")
        return None
    # 获得第一个文章的bibtex链接
    bibtex_link = elements[0].attrib["href"]
    # 将".html?view=bibtex"替换为".bib"
    if source_settings.keyword_regex:
        for old, new in source_settings.keyword_regex.items():
            bibtex_link = bibtex_link.replace(old, new)
    # get bibtex result
    try:
        res = requests.get(bibtex_link, headers=headers)
    except Exception as e:
        logger.error(f"Error occur when fetching {bibtex_link}: {e}")
        return None
    return res.text


def get_bibtex(config: Config, query: str, source="google_scholar"):
    if source in ["google_scholar", "dblp"]:
        return get_bibtex_common(config, query, source)
    else:
        raise NotImplementedError("{} is not supported yet.".format(source))
