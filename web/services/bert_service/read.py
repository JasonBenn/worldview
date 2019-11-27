from bert_serving.client import BertClient


def get_bert_client():
    return BertClient(ip="192.168.86.176")
