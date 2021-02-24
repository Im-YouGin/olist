import pandas as pd
import os

from manage import load_django
from glob import glob
from django.db import transaction
from warnings import filterwarnings
filterwarnings('ignore')

load_django()

from ecommerce.models import (StageItem, StageOrder, StageCategory, StageCustomer,
                      StageGeolocation, StagePayment, StageProduct, StageSeller)

data_dir = os.path.join(os.path.dirname(__file__), 'raw_data')
test_dir = os.path.join(os.path.dirname(__file__), 'test_data')


def update_stage_model(model, f_path):
    df = pd.read_csv(f_path, dtype={
        'customer_zip_code_prefix': str,
        'geolocation_zip_code_prefix': str,
        'seller_zip_code_prefix': str
    })
    df = df.where(pd.notna(df), None)

    model.objects.all().delete()
    model.objects.bulk_create([
        model(**row.to_dict()) for _, row in df.iterrows()
    ], batch_size=15000)


def update_all(data_dir):
    with transaction.atomic():
        for model, f_path in zip(
                (StageCustomer, StageGeolocation, StageOrder, StageItem,
                 StagePayment, StageProduct, StageSeller, StageCategory),
                glob(data_dir + r'\*.csv')
        ):
            print(model)
            update_stage_model(model, f_path)


if __name__ == '__main__':
    update_all(test_dir)

