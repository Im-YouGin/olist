import pandas as pd

from manage import load_django
load_django()

from ecommerce.models import *
from django.db import transaction
from django.db.models import Max
from datetime import datetime
from warnings import filterwarnings
from multiprocessing.pool import ThreadPool

filterwarnings('ignore')

# (Order, OrderDetail, Customer,
# ProductCategory, Payment, ShippingDetail,
# Product, Geolocation, Seller)


def get_next_id(model):
    max_id = model.objects.values('id').aggregate(Max('id'))['id__max']
    return 1 if max_id is None else max_id + 1


def fill_geolocation():
    raw_df = pd.DataFrame(
        StageGeolocation.objects.values()
    ).drop('id', axis=1)
    raw_df.columns = ['zip_code', 'lat', 'lon', 'city', 'state']
    raw_df = raw_df[raw_df['zip_code'].notna()]
    raw_df.drop_duplicates('zip_code', inplace=True)

    seen = set(Geolocation.objects.values_list('zip_code', flat=True))
    with transaction.atomic():
        for ix, row in raw_df.iterrows():
            row = row.to_dict()
            zip_code = row.pop('zip_code')

            if zip_code in seen:
                geo = Geolocation.objects.get(
                    zip_code=zip_code, current_flag=True)

                if list(geo.__dict__.values())[7:] != list(row.values()):
                    geo.current_flag = False
                    geo.period_to = datetime.now()
                    geo.save()

                    new_obj = Geolocation.objects.create(
                        id=geo.id,
                        zip_code=zip_code,
                        **row
                    )

                    Customer.objects.filter(geolocation=geo).update(geolocation=new_obj)
                    Seller.objects.filter(geolocation=geo).update(geolocation=new_obj)
            else:
                Geolocation.objects.create(
                    id=get_next_id(Geolocation),
                    zip_code=zip_code,
                    **row
                )
                seen.add(zip_code)


def fill_product_category():
    raw_df = pd.DataFrame(StageCategory.objects.values()).drop('id', axis=1)
    raw_df.columns = ['name', 'translated_name']
    raw_df = raw_df[raw_df['name'].notna()]
    raw_df.drop_duplicates('name', inplace=True)

    seen = set(ProductCategory.objects.values_list('name', flat=True))
    with transaction.atomic():
        for ix, row in raw_df.iterrows():
            row = row.to_dict()
            name = row.pop('name')

            if name in seen:
                cat = ProductCategory.objects.get(
                    name=name, current_flag=True)

                if list(cat.__dict__.values())[-1:] != list(row.values()):
                    cat.current_flag = False
                    cat.period_to = datetime.now()
                    cat.save()

                    new_obj = ProductCategory.objects.create(
                        id=cat.id,
                        name=name,
                        **row
                    )

                    Product.objects.filter(category=cat).update(category=new_obj)
            else:
                ProductCategory.objects.create(
                    id=get_next_id(ProductCategory),
                    name=name,
                    **row
                )
                seen.add(name)


def get_customer_obj(row):
    geo = Geolocation.objects.filter(
        zip_code=row['customer_zip_code_prefix'], current_flag=True).first()
    cust = Customer.objects.filter(
        customer_key=row['customer_id'], current_flag=True).first()

    if cust is not None:
        if cust.geolocation != geo:
            cust.current_flag = False
            cust.period_to = datetime.now()
            cust.save()

            new_obj = Customer.objects.create(
                id=cust.id,
                customer_key=row['customer_id'],
                geolocation=geo
            )

            return new_obj
        return cust

    return Customer.objects.create(
        id=get_next_id(Customer),
        customer_key=row['customer_id'],
        geolocation=geo
    )


def get_seller_obj(row):
    geo = Geolocation.objects.filter(
        zip_code=row['seller_zip_code_prefix'], current_flag=True).first()
    sell = Seller.objects.filter(
        seller_key=row['seller_id'], current_flag=True).first()

    if sell is not None:
        if sell.geolocation != geo:
            sell.current_flag = False
            sell.period_to = datetime.now()
            sell.save()

            new_obj = Seller.objects.create(
                id=sell.id,
                seller_key=row['seller_id'],
                geolocation=geo
            )

            return new_obj
        return sell

    return Seller.objects.create(
        id=get_next_id(Seller),
        seller_key=row['seller_id'],
        geolocation=geo
    )


def get_shipping_obj(row):
    order_det = OrderDetail.objects.filter(order_key=row['order_id'],
                                           current_flag=True).first()
    status, _ = OrderStatus.objects.get_or_create(status=row['order_status'])

    if order_det is not None:
        ship = order_det.shipping_detail

        if ship is not None:
            if (ship.status != status or
                ship.freight_value != row['freight_value'] or
                ship.shipping_lim_date != row['shipping_limit_date'] or
                ship.purchased_at != row['order_purchase_timestamp'] or
                ship.approved_at != row['order_approved_at'] or
                ship.delivered_carrier != row['order_delivered_carrier_date'] or
                ship.delivered_customer != row['order_delivered_customer_date'] or
                ship.estimated_delivery != row['order_estimated_delivery_date']
            ):
                print('+')

                ship.current_flag = False
                ship.period_to = datetime.now()
                ship.save()

                new_obj = ShippingDetail.objects.create(
                    id=ship.id,
                    status=status,
                    freight_value=row['freight_value'],
                    shipping_lim_date=row['shipping_limit_date'],
                    purchased_at=row['order_purchase_timestamp'],
                    approved_at=row['order_approved_at'],
                    delivered_carrier=row['order_delivered_carrier_date'],
                    delivered_customer=row['order_delivered_customer_date'],
                    estimated_delivery=row['order_estimated_delivery_date']
                )

                OrderDetail.objects.filter(shipping_detail=ship).update(
                    shipping_detail=new_obj)

                return new_obj
            return ship

    return ShippingDetail.objects.create(
            id=get_next_id(ShippingDetail),
            status=status,
            freight_value=row['freight_value'],
            shipping_lim_date=row['shipping_limit_date'],
            purchased_at=row['order_purchase_timestamp'],
            approved_at=row['order_approved_at'],
            delivered_carrier=row['order_delivered_carrier_date'],
            delivered_customer=row['order_delivered_customer_date'],
            estimated_delivery=row['order_estimated_delivery_date']
        )


def get_order_detail_obj(row, shipping_detail):
    det = OrderDetail.objects.filter(order_key=row['order_id'],
                                     current_flag=True).first()
    payment_method, _ = PaymentMethod.objects.get_or_create(
        method=row['payment_type'])

    if det is not None:
        if (det.n_items != row['order_item_id'] or
            det.payment_value != row['payment_value'] or
            det.payment_method != payment_method or
            det.shipping_detail != shipping_detail
        ):
            det.current_flag = False
            det.period_to = datetime.now()
            det.save()

            new_obj = OrderDetail.objects.create(
                id=det.id,
                order_key=row['order_id'],
                n_items=row['order_item_id'],
                payment_value=row['payment_value'],
                payment_method=payment_method,
                shipping_detail=shipping_detail
            )

            return new_obj
        return det

    return OrderDetail.objects.create(
        id=get_next_id(OrderDetail),
        order_key=row['order_id'],
        n_items=row['order_item_id'],
        payment_value=row['payment_value'],
        payment_method=payment_method,
        shipping_detail=shipping_detail
    )


def get_product_obj(row):
    cat = ProductCategory.objects.filter(
        name=row['product_category_name']).first()
    prod = Product.objects.filter(
        product_key=row['product_id'], current_flag=True).first()

    if prod is not None:
        if (
            prod.price != row['price'] or
            prod.weight != row['product_weight_g'] or
            prod.length != row['product_length_cm'] or
            prod.height != row['product_height_cm'] or
            prod.width != row['product_width_cm'] or
            prod.category != cat
        ):
            prod.current_flag = False
            prod.period_to = datetime.now()
            prod.save()

            new_obj = Product.objects.create(
                id=prod.id,
                product_key=row['product_id'],
                price=row['price'],
                weight=row['product_weight_g'],
                length=row['product_length_cm'],
                height=row['product_height_cm'],
                width=row['product_width_cm'],
                category=cat
            )

            # Order.objects.filter(product=prod).update(product=new_obj)

            return new_obj
        return prod

    return Product.objects.create(
        id=get_next_id(Product),
        product_key=row['product_id'],
        price=row['price'],
        weight=row['product_weight_g'],
        length=row['product_length_cm'],
        height=row['product_height_cm'],
        width=row['product_width_cm'],
        category=cat
    )


def fill_order():
    i = 0

    def process_one_order(row):
        global l
        nonlocal i
        # customer object
        customer = get_customer_obj(row)

        # seller object
        seller = get_seller_obj(row)

        # shipping object
        shipping = get_shipping_obj(row)

        # detail object
        detail = get_order_detail_obj(row, shipping)

        # product object
        product = get_product_obj(row)

        # payment object
        i += 1
        if not i % 10000:
            print(f'{i} / {l}')
        return Order(
            customer=customer,
            seller=seller,
            detail=detail,
            product=product
        )

    raw_payment = pd.DataFrame(
        StagePayment.objects.values('order_id', 'payment_type', 'payment_value')
    )
    raw_order = pd.DataFrame(
        StageOrder.objects.values()
    )
    raw_seller = pd.DataFrame(
        StageSeller.objects.values('seller_id', 'seller_zip_code_prefix')
    )
    raw_product = pd.DataFrame(
        StageProduct.objects.values()
    )
    raw_item = pd.DataFrame(
        StageItem.objects.values()
    )
    raw_customer = pd.DataFrame(
        StageCustomer.objects.values('customer_id', 'customer_zip_code_prefix')
    )
    order = pd.merge(raw_order, raw_item, on='order_id')
    order = pd.merge(order, raw_payment, on='order_id')
    order = pd.merge(order, raw_seller, on='seller_id')
    order = pd.merge(order, raw_customer, on='customer_id')
    order = pd.merge(order, raw_product, on='product_id')

    order = order.astype(object).where(pd.notna(order), None)
    order = order.drop(['id_x', 'id_y', 'id'], axis=1).drop_duplicates()
    global l
    l = order.shape[0]

    with ThreadPool(processes=1) as p:
        objs = p.map(
            process_one_order, [row.to_dict() for ix, row in order.iterrows()][:1000])
    Order.objects.bulk_create([x for x in objs if x is not None], batch_size=15000)


if __name__ == '__main__':
    fill_product_category()
    fill_geolocation()
    fill_order()

