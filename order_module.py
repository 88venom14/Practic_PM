# -*- coding: utf-8 -*-
# Проверка и обработка данных заказов интернет-магазина.
# Только стандартная библиотека, без сети и сторонних пакетов.

import re
from dataclasses import dataclass, field
from typing import Optional


# Валюты, с которыми работаем (коды по ISO 4217).
SUPPORTED_CURRENCIES = {"RUB", "USD", "EUR", "CNY", "GBP"}

# Шаблон почты: ловит частые ошибки, не претендуя на весь RFC.
_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# Шаблон артикула: латиница, цифры и дефис, длина от 3 до 32 символов.
_SKU_PATTERN = re.compile(r"^[A-Z0-9\-]{3,32}$")


# Своя ошибка для данных, не прошедших проверку.
class ValidationError(Exception):
    pass


# Одна позиция заказа: артикул, количество, цена за штуку.
@dataclass
class OrderItem:
    sku: str
    quantity: int
    price: float


# Заказ целиком: номер, почта покупателя, валюта и список позиций.
@dataclass
class Order:
    order_id: str
    customer_email: str
    currency: str
    items: list = field(default_factory=list)


def validate_email(email: str) -> str:
    if not isinstance(email, str):
        raise ValidationError("Адрес электронной почты должен быть строкой.")
    # Чистим пробелы и нижний регистр, чтобы не плодить дубли.
    normalized = email.strip().lower()
    if not normalized:
        raise ValidationError("Адрес электронной почты не может быть пустым.")
    if not _EMAIL_PATTERN.match(normalized):
        raise ValidationError(f"Некорректный формат адреса электронной почты: {email!r}.")
    return normalized


def validate_sku(sku: str) -> str:
    if not isinstance(sku, str):
        raise ValidationError("Артикул товара должен быть строкой.")
    # Держим артикулы в верхнем регистре, чтобы не разъезжались.
    normalized = sku.strip().upper()
    if not normalized:
        raise ValidationError("Артикул товара не может быть пустым.")
    if not _SKU_PATTERN.match(normalized):
        raise ValidationError(
            f"Некорректный артикул товара: {sku!r}. "
            "Допустимы латинские буквы, цифры и дефис, длина от 3 до 32 символов."
        )
    return normalized


def validate_currency(currency: str) -> str:
    if not isinstance(currency, str):
        raise ValidationError("Код валюты должен быть строкой.")
    normalized = currency.strip().upper()
    if normalized not in SUPPORTED_CURRENCIES:
        raise ValidationError(
            f"Неподдерживаемая валюта: {currency!r}. "
            f"Доступные валюты: {', '.join(sorted(SUPPORTED_CURRENCIES))}."
        )
    return normalized


def validate_quantity(quantity: int) -> int:
    # bool в Python это тоже int, поэтому отсекаем его отдельно.
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValidationError("Количество товара должно быть целым числом.")
    if quantity <= 0:
        raise ValidationError("Количество товара должно быть больше нуля.")
    return quantity


def validate_price(price: float) -> float:
    # Ноль разрешаем (подарок), а вот минус нет.
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        raise ValidationError("Цена товара должна быть числом.")
    if price < 0:
        raise ValidationError("Цена товара не может быть отрицательной.")
    return float(price)


def validate_item(item: OrderItem) -> OrderItem:
    if not isinstance(item, OrderItem):
        raise ValidationError("Позиция заказа должна быть объектом OrderItem.")
    # Возвращаем новую позицию с уже проверенными полями.
    return OrderItem(
        sku=validate_sku(item.sku),
        quantity=validate_quantity(item.quantity),
        price=validate_price(item.price),
    )


def validate_order(order: Order) -> Order:
    if not isinstance(order, Order):
        raise ValidationError("Заказ должен быть объектом Order.")

    # Номер заказа не может быть пустым.
    if not isinstance(order.order_id, str) or not order.order_id.strip():
        raise ValidationError("Идентификатор заказа не может быть пустым.")

    # Пустой заказ тоже не имеет смысла.
    if not order.items:
        raise ValidationError("Заказ должен содержать хотя бы одну позицию.")

    # Каждую позицию проверяем отдельно.
    validated_items = [validate_item(item) for item in order.items]

    return Order(
        order_id=order.order_id.strip(),
        customer_email=validate_email(order.customer_email),
        currency=validate_currency(order.currency),
        items=validated_items,
    )


def calculate_order_total(
    order: Order, discount_percent: float = 0.0
) -> float:
    # Сначала проверяем заказ, чтобы не считать по плохим данным.
    validated = validate_order(order)

    if isinstance(discount_percent, bool) or not isinstance(
        discount_percent, (int, float)
    ):
        raise ValidationError("Размер скидки должен быть числом.")
    if not 0 <= discount_percent <= 100:
        raise ValidationError("Размер скидки должен быть в диапазоне от 0 до 100 процентов.")

    # Сумма позиций, затем скидка, затем округление до копеек.
    subtotal = sum(item.price * item.quantity for item in validated.items)
    total = subtotal * (1 - discount_percent / 100)
    return round(total, 2)


def format_price(amount: float, currency: str) -> str:
    valid_amount = validate_price(amount)
    valid_currency = validate_currency(currency)
    # Меняем запятую-разделитель на пробел: вид "1 234.50".
    formatted_number = f"{valid_amount:,.2f}".replace(",", " ")
    return f"{formatted_number} {valid_currency}"


if __name__ == "__main__":
    # Быстрый пример, чтобы посмотреть, как всё работает.
    demo_order = Order(
        order_id="ORD-1001",
        customer_email="Buyer@Example.com",
        currency="usd",
        items=[
            OrderItem(sku="abc-123", quantity=2, price=49.90),
            OrderItem(sku="xyz-777", quantity=1, price=100.00),
        ],
    )
    checked = validate_order(demo_order)
    total = calculate_order_total(demo_order, discount_percent=10)
    print("Проверенный заказ:", checked)
    print("Итог со скидкой 10%:", format_price(total, checked.currency))
