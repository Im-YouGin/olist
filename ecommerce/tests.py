# import os
#
# from ecommerce.orders.fill_stage import update_all, data_dir
# from ecommerce.orders.fill_orders import *
# from django.test import TestCase, TransactionTestCase
# from ecommerce.models import *
# # Create your tests here.
# import unittest
# from django.db import connection
#
# test_dir = os.path.join(os.path.dirname(__file__), 'orders',
#                         'test_data')
#
# test_order_key = '035b790fa740b68de2d6f1a74f9b2098'
#
#
# class OrderTest(unittest.TestCase):
#
#     def test_full_loading(self):
#         with connection.cursor() as cursor:
#             cursor.execute(
#                 """
#                 delete from orders_order;
#
#                 delete from orders_customer;
#
#                 delete from orders_order_detail;
#
#                 delete from orders_payment;
#
#                 delete from orders_product;
#
#                 delete from orders_product_category;
#
#                 delete from orders_seller;
#
#                 delete from orders_geolocation;
#                 """
#             )
#         update_all(data_dir)
#         fill_geolocation()
#         fill_product_category()
#         fill_order()
#
#         self.assertEqual(
#             ProductCategory.objects.get(
#                 name='beleza_saude', current_flag=True).translated_name,
#             'health_beauty')
#         self.assertEqual(
#             Geolocation.objects.get(zip_code='04403').city,
#             'sao paulo')
#         self.assertFalse(
#             ProductCategory.objects.filter(
#                 name='recreation_leisure', current_flag=True).exists())
#
#         test_order_obj = Order.objects.get(
#             detail__order_key=test_order_key)
#
#         self.assertEqual(test_order_obj.detail.n_items, 1)
#         self.assertIsNone(test_order_obj.shipping_detail.delivered_customer)
#         self.assertEqual(test_order_obj.payment.value, 72.28)
#         self.assertEqual(test_order_obj.product.weight, 900)
#
#     def test_incremental_loading(self):
#         update_all(test_dir)
#         fill_geolocation()
#         fill_product_category()
#         fill_order()
#
#         test_order_obj = Order.objects.get(
#             detail__order_key=test_order_key)
#
#         self.assertEqual(
#             ProductCategory.objects.get(
#                 name='beleza_saude', current_flag=True).translated_name,
#             'health_and_beauty')
#         self.assertEqual(
#             Geolocation.objects.all().get(zip_code='04403').city,
#             'sao paulo city')
#         self.assertTrue(
#             ProductCategory.objects.filter(
#                 name='recreation_leisure', current_flag=True).exists())
#
#         self.assertEqual(test_order_obj.detail.n_items, 2)
#         self.assertIsNotNone(test_order_obj.shipping_detail.delivered_customer)
#         self.assertEqual(test_order_obj.payment.value, 144.56)
#         self.assertEqual(test_order_obj.product.weight, 1000)
