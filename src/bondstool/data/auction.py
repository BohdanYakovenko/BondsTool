import io
import zipfile
from xml.etree.cElementTree import XML, Element

import pandas as pd
import requests
from bs4 import BeautifulSoup

AUC_DOMAIN = "https://mof.gov.ua"
AUC_URL = AUC_DOMAIN + "/uk/ogoloshennja-ta-rezultati-aukcioniv"
ISIN_PREFIX = "UA4000"


def get_doc_url_date():

    resp = requests.get(AUC_URL)

    soup = BeautifulSoup(resp.text, features="html.parser")

    auc_date = soup.table.select("td")[0].contents[0]

    doc_path = soup.table.select('a[href*=".docx"]')[0]["href"]

    doc_url = AUC_DOMAIN + doc_path

    return doc_url, auc_date


def get_auction_xml(url):

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
    for paragraph in tree.iter(PARA):
        texts = [node.text for node in paragraph.iter(TEXT) if node.text]
        if texts:
            texts = "".join(texts)

            if ISIN_PREFIX in texts:
                isins.append(texts)

    return pd.DataFrame({"ISIN": isins})


def filter_trading_bonds(isin_df: pd.DataFrame, bonds: pd.DataFrame):
    return isin_df.merge(bonds, how="left")
