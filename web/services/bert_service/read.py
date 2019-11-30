from bert_serving.client import BertClient


def get_bert_client():
    # return BertClient(ip="192.168.86.176")  # if in Aperture Science
    return BertClient()  # requires active SSH tunnel with local forwards on 5555 and 5556
