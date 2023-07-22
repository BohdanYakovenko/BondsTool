import io
import zipfile
from xml.etree.cElementTree import XML, Element

import pandas as pd
import requests
from bondstool.data.bag import ISIN_PREFIX

DOC_URL = "https://mof.gov.ua/storage/files/121-123%20%D0%BE%D0%B3%D0%BE%D0%BB%D0%BE%D1%88%D0%B5%D0%BD%D0%BD%D1%8F.docx"


def get_auction_xml(url=DOC_URL):

    resp = requests.get(url)

    zip = zipfile.ZipFile(io.BytesIO(resp.content))

    xml_content = zip.read("word/document.xml")
    zip.close()

    return XML(xml_content)


def parse_xml_isins(tree: Element):

    WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    PARA = WORD_NAMESPACE + "p"
    TEXT = WORD_NAMESPACE + "t"

    isins = []
    for paragraph in tree.getiterator(PARA):
        texts = [node.text for node in paragraph.getiterator(TEXT) if node.text]
        if texts:
            texts = "".join(texts)

            if ISIN_PREFIX in texts:
                isins.append(texts)

    return pd.DataFrame({"ISIN": isins})


def filter_trading_bonds(isin_df: pd.DataFrame, bonds: pd.DataFrame):

    return isin_df.merge(bonds, how="left")
