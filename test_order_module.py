# -*- coding: utf-8 -*-
# Тесты для order_module.py на стандартном unittest.
# Запуск: python -m unittest test_order_module

import unittest

from order_module import (
    Order,
    OrderItem,
    ValidationError,
    calculate_order_total,
    format_price,
    validate_currency,
    validate_email,
    validate_order,
    validate_price,
    validate_quantity,
    validate_sku,
)


# Проверяем работу с почтой покупателя.
class TestValidateEmail(unittest.TestCase):

    def test_корректный_адрес_нормализуется(self):
        # Пробелы убираются, буквы становятся строчными.
        self.assertEqual(validate_email("  User@Mail.COM "), "user@mail.com")

    def test_адрес_без_собачки_отклоняется(self):
        # Без @ это не адрес, ждём ошибку.
        with self.assertRaises(ValidationError):
            validate_email("usermail.com")

    def test_пустой_адрес_отклоняется(self):
        # Одни пробелы за адрес не считаются.
        with self.assertRaises(ValidationError):
            validate_email("   ")

    def test_адрес_неверного_типа_отклоняется(self):
        # Не строка, значит тоже ошибка.
        with self.assertRaises(ValidationError):
            validate_email(12345)


# Проверяем артикулы товаров.
class TestValidateSku(unittest.TestCase):

    def test_корректный_артикул_в_верхнем_регистре(self):
        # Артикул приходит в верхнем регистре.
        self.assertEqual(validate_sku("abc-123"), "ABC-123")

    def test_слишком_короткий_артикул_отклоняется(self):
        # Меньше трёх символов не пропускаем.
        with self.assertRaises(ValidationError):
            validate_sku("ab")

    def test_артикул_с_недопустимыми_символами_отклоняется(self):
        # Пробелы и знаки внутри артикула недопустимы.
        with self.assertRaises(ValidationError):
            validate_sku("ABC 123!")


# Проверяем коды валют.
class TestValidateCurrency(unittest.TestCase):

    def test_поддерживаемая_валюта(self):
        # Код приводится к верхнему регистру.
        self.assertEqual(validate_currency("usd"), "USD")

    def test_неизвестная_валюта_отклоняется(self):
        # Валюту не из списка не принимаем.
        with self.assertRaises(ValidationError):
            validate_currency("XYZ")


# Проверяем количество и цену.
class TestValidateQuantityAndPrice(unittest.TestCase):

    def test_положительное_количество(self):
        # Обычное положительное число проходит.
        self.assertEqual(validate_quantity(5), 5)

    def test_нулевое_количество_отклоняется(self):
        # Ноль штук заказать нельзя.
        with self.assertRaises(ValidationError):
            validate_quantity(0)

    def test_булево_количество_отклоняется(self):
        # True не должно сойти за единицу.
        with self.assertRaises(ValidationError):
            validate_quantity(True)

    def test_отрицательная_цена_отклоняется(self):
        # Цена в минус это ошибка.
        with self.assertRaises(ValidationError):
            validate_price(-1.0)

    def test_нулевая_цена_допустима(self):
        # Ноль допустим (подарок) и возвращается как float.
        self.assertEqual(validate_price(0), 0.0)


# Проверяем заказ целиком.
class TestValidateOrder(unittest.TestCase):

    def setUp(self):
        # Один корректный заказ для нескольких тестов.
        self.valid_order = Order(
            order_id="ORD-1",
            customer_email="buyer@example.com",
            currency="RUB",
            items=[OrderItem(sku="abc-123", quantity=2, price=100.0)],
        )

    def test_корректный_заказ_проходит_проверку(self):
        # У хорошего заказа данные приводятся к норме.
        checked = validate_order(self.valid_order)
        self.assertEqual(checked.items[0].sku, "ABC-123")
        self.assertEqual(checked.currency, "RUB")

    def test_заказ_без_позиций_отклоняется(self):
        # Пустой заказ принимать нельзя.
        empty_order = Order(
            order_id="ORD-2",
            customer_email="buyer@example.com",
            currency="RUB",
            items=[],
        )
        with self.assertRaises(ValidationError):
            validate_order(empty_order)

    def test_пустой_идентификатор_заказа_отклоняется(self):
        # Номер заказа не может быть из одних пробелов.
        self.valid_order.order_id = "   "
        with self.assertRaises(ValidationError):
            validate_order(self.valid_order)


# Проверяем расчёт суммы заказа.
class TestCalculateOrderTotal(unittest.TestCase):

    def setUp(self):
        self.order = Order(
            order_id="ORD-3",
            customer_email="buyer@example.com",
            currency="USD",
            items=[
                OrderItem(sku="abc-123", quantity=2, price=50.0),
                OrderItem(sku="xyz-777", quantity=1, price=100.0),
            ],
        )

    def test_итог_без_скидки(self):
        # 2 по 50 плюс 1 по 100 = 200.
        self.assertEqual(calculate_order_total(self.order), 200.0)

    def test_итог_со_скидкой(self):
        # Скидка 10%: 200 * 0.9 = 180.
        self.assertEqual(calculate_order_total(self.order, discount_percent=10), 180.0)

    def test_скидка_вне_диапазона_отклоняется(self):
        # Скидку больше 100% не принимаем.
        with self.assertRaises(ValidationError):
            calculate_order_total(self.order, discount_percent=150)


# Проверяем форматирование цены.
class TestFormatPrice(unittest.TestCase):

    def test_форматирование_с_разделителем_разрядов(self):
        # Разряды через пробел, в конце код валюты.
        self.assertEqual(format_price(1234.5, "rub"), "1 234.50 RUB")

    def test_форматирование_неподдерживаемой_валюты_отклоняется(self):
        # Неизвестная валюта роняет и форматирование.
        with self.assertRaises(ValidationError):
            format_price(100.0, "ZZZ")


if __name__ == "__main__":
    unittest.main()
