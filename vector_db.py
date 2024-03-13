from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

available_items = [
    "Mazanec 400 gramů",
    "Mazanec s rozinkami sypaný mandlemi 400 gramů",
    "Mazanec máslový 400 gramů",
    "Vánočka s rozinkami 200 gramů",
    "Vánočka 400 gramů",
    "Vánočka máslová rozinková manandlová 600 gramů",
    "Vánočka s rozinkami a mandlemi 5 kůsů po 400 gramech",
    "Špička s náplní makovou 2 kusy po 110 gramech",
    "Špička s náplní makovou a tvarohovou 2 kusy po 110 gramech",
    "Chléb konzumní s kmínem 1200 gramů",
    "Chléb konzumní s kmínem 500 gramů",
    "Chléb s kmínem Šumava 6 krát 570 gramů",
    "Zelňák 30 gramů - předpečený",
    "Rohlík 43 gramů",
    "Raženka bez posyp. 30 krát 60 gramů",
    "Bábovky MIX 2400 gramů",
    "Klimentovský chléb - jedlá etiketa 800 gramů",
    "Tesco Finest Vícezrnný chléb s quinoou 500 gramů"
]

available_items_db = FAISS.from_texts(available_items, embeddings)