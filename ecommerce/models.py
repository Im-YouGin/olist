from django.db import models
from datetime import datetime


class HistoryBase(models.Model):
    surrogate_id = models.AutoField(primary_key=True)
    id = models.IntegerField()
    current_flag = models.BooleanField(default=True)
    period_from = models.DateTimeField(default=datetime.now())
    period_to = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class PaymentMethod(models.Model):
    method = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'orders_payment_method'


class OrderStatus(models.Model):
    status = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'orders_order_status'


class ShippingDetail(HistoryBase):
    status = models.ForeignKey(OrderStatus, null=True, on_delete=models.SET_NULL)
    freight_value = models.FloatField()
    shipping_lim_date = models.DateTimeField()
    purchased_at = models.DateTimeField()
    approved_at = models.DateTimeField(null=True)
    delivered_carrier = models.DateTimeField(null=True)
    delivered_customer = models.DateTimeField(null=True)
    estimated_delivery = models.DateTimeField()

    class Meta:
        db_table = 'orders_shipping_detail'


class OrderDetail(HistoryBase):
    order_key = models.CharField(max_length=255)
    n_items = models.IntegerField(null=True)
    payment_value = models.FloatField()
    payment_method = models.ForeignKey(PaymentMethod, null=True,
                                       on_delete=models.SET_NULL)
    shipping_detail = models.ForeignKey(ShippingDetail, null=True,
                                        on_delete=models.SET_NULL)

    class Meta:
        db_table = 'orders_order_detail'


class ProductCategory(HistoryBase):
    name = models.CharField(max_length=255)
    translated_name = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'orders_product_category'


class Product(HistoryBase):
    product_key = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, null=True,
                                 on_delete=models.SET_NULL)
    price = models.FloatField()
    weight = models.FloatField(null=True)
    length = models.FloatField(null=True)
    height = models.FloatField(null=True)
    width = models.FloatField(null=True)

    class Meta:
        db_table = 'orders_product'


class Geolocation(HistoryBase):
    zip_code = models.CharField(max_length=10)
    lat = models.FloatField()
    lon = models.FloatField()
    city = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=2, null=True)

    class Meta:
        db_table = 'orders_geolocation'


class Seller(HistoryBase):
    seller_key = models.CharField(max_length=255)
    geolocation = models.ForeignKey(Geolocation, null=True,
                                    on_delete=models.SET_NULL)

    class Meta:
        db_table = 'orders_seller'


class Customer(HistoryBase):
    customer_key = models.CharField(max_length=255)
    geolocation = models.ForeignKey(Geolocation, null=True,
                                    on_delete=models.SET_NULL)

    class Meta:
        db_table = 'orders_customer'


class Order(models.Model):
    detail = models.ForeignKey(OrderDetail, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    seller = models.ForeignKey(Seller, null=True, on_delete=models.SET_NULL)
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'orders_order'


class StageCustomer(models.Model):
    customer_id = models.CharField(max_length=255, null=True)
    customer_unique_id = models.CharField(max_length=255, null=True)
    customer_zip_code_prefix = models.CharField(max_length=10)
    customer_city = models.CharField(max_length=255, null=True)
    customer_state = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'orders_stage_customer'


class StageGeolocation(models.Model):
    geolocation_zip_code_prefix = models.CharField(max_length=10, null=True)
    geolocation_lat = models.FloatField(null=True)
    geolocation_lng = models.FloatField(null=True)
    geolocation_city = models.CharField(max_length=255, null=True)
    geolocation_state = models.CharField(max_length=2, null=True)

    class Meta:
        db_table = 'orders_stage_geolocation'


class StageItem(models.Model):
    order_id = models.CharField(max_length=255)
    order_item_id = models.IntegerField(null=True)
    product_id = models.CharField(max_length=255)
    seller_id = models.CharField(max_length=255)
    shipping_limit_date = models.DateTimeField(null=True)
    price = models.FloatField(null=True)
    freight_value = models.FloatField(null=True)

    class Meta:
        db_table = 'orders_stage_item'


class StagePayment(models.Model):
    order_id = models.CharField(max_length=255, null=True)
    payment_sequential = models.IntegerField(null=True)
    payment_type = models.CharField(max_length=255, null=True)
    payment_installments = models.IntegerField(null=True)
    payment_value = models.FloatField(null=True)

    class Meta:
        db_table = 'orders_stage_payment'


class StageOrder(models.Model):
    order_id = models.CharField(max_length=255, null=True)
    customer_id = models.CharField(max_length=255, null=True)
    order_status = models.CharField(max_length=255, null=True)
    order_purchase_timestamp = models.DateTimeField(null=True)
    order_approved_at = models.DateTimeField(null=True)
    order_delivered_carrier_date = models.DateTimeField(null=True)
    order_delivered_customer_date = models.DateTimeField(null=True)
    order_estimated_delivery_date = models.DateTimeField(null=True)

    class Meta:
        db_table = 'orders_stage_order'


class StageProduct(models.Model):
    product_id = models.CharField(max_length=255, null=True)
    product_category_name = models.CharField(max_length=255, null=True)
    product_name_lenght = models.IntegerField(null=True)
    product_description_lenght = models.IntegerField(null=True)
    product_photos_qty = models.IntegerField(null=True)
    product_weight_g = models.FloatField(null=True)
    product_length_cm = models.FloatField(null=True)
    product_height_cm = models.FloatField(null=True)
    product_width_cm = models.FloatField(null=True)

    class Meta:
        db_table = 'orders_stage_product'


class StageSeller(models.Model):
    seller_id = models.CharField(max_length=255, null=True)
    seller_zip_code_prefix = models.CharField(max_length=10, null=True)
    seller_city = models.CharField(max_length=255, null=True)
    seller_state = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'orders_stage_seller'


class StageCategory(models.Model):
    product_category_name = models.CharField(max_length=255, null=True)
    product_category_name_english = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = 'orders_stage_category'


