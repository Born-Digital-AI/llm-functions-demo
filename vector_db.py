import os

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


os.environ["OPENAI_API_KEY"] = "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"

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

available_items = [
    "Mazanec 400g",
    "Mazanec s rozinkami sypaný mandlemi 400g",
    "Mazanec máslový 400g",
    "Vánočka s rozinkami 200g",
    "Vánočka 400g",
    "Vánočka máslová rozinková manandlová 600g",
    "Vánočka s rozinkami a mandlemi 5 ks á 400g 2000g",
    "Špička s náplní makovou 2ks á 110g",
    "Špička s náplní makovou a tvarohovou 2ks á110g",
    "Chléb konzumní s kmínem 1200g",
    "Chléb konzumní s kmínem 500g - předpečený BIDVEST",
    "Chléb s kmínem Šumava 6x570g 3420gBK",
    "Zelňák 30g - předpečený",
    "Rohlík 43g",
    "Raženka bez posyp. 30x60g",
    "Bábovky MIX (3ks mramorová 400g, 3ks šlehaná 400g) 2400g",
    "Klimentovský chléb (jedlá etiketa) 800g",
    "Tesco Finest Vícezrnný chléb s quinoou 500g"
]

available_items_db = FAISS.from_texts(available_items, embeddings)