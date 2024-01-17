from config import KEY, SECRET
from data_handler import DataHandler


def get_info_data():
    data = DataHandler(KEY, SECRET)
    infobijeenkomst_form = data.get_info_forms()
    info_name = list(infobijeenkomst_form.keys())
    return infobijeenkomst_form, info_name
