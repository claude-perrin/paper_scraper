from collections import namedtuple

Price = namedtuple('Price', ['price'])
Delivery = namedtuple('Delivery', ['delivery_type', 'price'])
ProductOption = namedtuple('ProductOption', ['option', 'delivery'])
Product = namedtuple('Product', ['product_title', 'product_link', 'product_option'])
Subcategory = namedtuple('Subcategory', ['subcategory_title', 'product'])
Category = namedtuple('Category', ['category_title', 'subcategory'])

category_1 = Category(category_title='Pets',
                      subcategory=[
                          Subcategory(
                              subcategory_title='toys',
                              product=[
                                  Product(
                                      product_title='fake_bone',
                                      product_link='./fake_bone',
                                      product_option=[
                                          ProductOption(
                                              option='small_size',
                                              delivery=[
                                                  Delivery(
                                                      delivery_type='nova_poshta',
                                                      price=[Price(price='50'), Price(price='100')]
                                                  ),
                                                  Delivery(
                                                      delivery_type='ukr_poshta',
                                                      price=[Price(price='20'), Price(price='30'),
                                                             Price(price='40')]
                                                  ),
                                              ]
                                          ),
                                      ]
                                  )
                              ]
                          )
                      ]
                      )
for subcategory in category_1.subcategory:
    for product in subcategory.product:
        for option in product.product_option:
            for delivery in option.delivery:
                for price in delivery.price:
                    print(subcategory.subcategory_title)
                    print(product.product_title)
                    print(option.option)
                    print(delivery.delivery_type)
                    print(price.price)
                    print('====')
