"""Test ES1: As a customer, I'd like to be able to place food orders."""
import pytest
from app.core.models.inventory import Stock, Item, IngredientGroup
from app.core.models.order import Order, OrderStatus
from app.core.models.user import User, UserType
from app.core.models import db


def login(client, email, password):
  return client.post(
      '/accounts/signin',
      data={
          "email": email,
          "password": password
      },
      follow_redirects=True)


def test_create_order(app):
  """Test creating order and adding items to it"""
  with app.app_context():
    sburger = Stock(name="burger", amount=3)
    swrap = Stock(name="wrap", amount=0)
    db.session.add(sburger)
    db.session.add(swrap)
    imain = Item(name="main")
    iburger = Item(name="burger")
    iwrap = Item(name="wrap")
    gtype = IngredientGroup(
        name="type", min_item=1, max_item=1, min_option=1, max_option=1)
    db.session.add(imain)
    db.session.add(iburger)
    db.session.add(iwrap)
    db.session.add(gtype)
    sburger.items.append(iburger)
    swrap.items.append(iwrap)
    gtype.options.append(iburger)
    gtype.options.append(iwrap)
    imain.ingredientgroups.append(gtype)
    db.session.commit()

    order = Order()
    order.AddRootItem(imain.GetID(), 1)
    order.AddIG("0.0", [iburger.GetID()], [1])
    order.AddRootItem(imain.GetID(), 1)
    with pytest.raises(RuntimeError):
      order.AddIG("0.0", [iburger.GetID()], [1])
    with pytest.raises(ValueError):
      order.AddIG("1.0", [iburger.GetID()], [2])
    with pytest.raises(ValueError):
      order.AddIG("1.0", [], [])
    with pytest.raises(RuntimeError):
      order.AddIG("1.0", [iwrap.GetID()], [1])
    swrap.IncreaseAmount(1)
    order.AddIG("1.0", [iwrap.GetID()], [1])


def test_order_details_string(app):
  """ Test order details are displayed correctly
  """
  with app.app_context():
    sburger = Stock(name="burger", amount=1)
    swrap = Stock(name="wrap", amount=1)
    db.session.add(sburger)
    db.session.add(swrap)
    imain = Item(name="main", price=0)
    iburger = Item(name="burger", price=5)
    iwrap = Item(name="wrap", price=3.3)
    gtype = IngredientGroup(
        name="type", min_item=1, max_item=1, min_option=1, max_option=1)
    db.session.add(imain)
    db.session.add(iburger)
    db.session.add(iwrap)
    db.session.add(gtype)
    sburger.items.append(iburger)
    swrap.items.append(iwrap)
    gtype.options.append(iburger)
    gtype.options.append(iwrap)
    imain.ingredientgroups.append(gtype)
    db.session.commit()

    order = Order()
    order.AddRootItem(imain.GetID(), 1)
    order.AddIG("0.0", [iburger.GetID()], [1])
    order.AddRootItem(imain.GetID(), 1)
    order.AddIG("1.0", [iwrap.GetID()], [1])

    assert order.GetDetailsString() == """main\n  type:burger ......$5.00\nmain
  type:wrap ......$3.30\n\n\nTotal price: $8.30"""


def test_pay_stock(app):
  """ Test stocks are correctly deducted after paid and order doesn't violate the
      stock level
  """

  with app.app_context():
    main = Item(name="Main", root=True)
    db.session.add(main)

    main_type_group = IngredientGroup(
        name="Main Type", max_item=1, min_item=1, max_option=1, min_option=1)

    main.ingredientgroups.append(main_type_group)
    db.session.add(main_type_group)

    burger = Item(name="Burger", root=False, price=10)
    db.session.add(burger)

    main_type_group.options.append(burger)
    bun_group = IngredientGroup(
        name="Bun", max_item=3, min_item=2, max_option=1, min_option=1)
    db.session.add(bun_group)
    burger.ingredientgroups.append(bun_group)

    muffin_bun = Item(name="Muffin Bun", root=False, identical=True, price=1)
    sesame_bun = Item(name="Sesame Bun", root=False, identical=True, price=2)
    standard_bun = Item(
        name="Standard Bun", root=False, identical=True, price=1)

    db.session.add(muffin_bun)
    db.session.add(sesame_bun)
    db.session.add(standard_bun)

    bun_group.options.append(muffin_bun)
    bun_group.options.append(sesame_bun)
    bun_group.options.append(standard_bun)

    wrap = Item(name="Wrap", root=False, price=5)
    db.session.add(wrap)
    main_type_group.options.append(wrap)

    patty_group = IngredientGroup(
        name="Patties", max_item=3, min_item=1, max_option=3, min_option=1)
    db.session.add(patty_group)
    main.ingredientgroups.append(patty_group)
    chicken_patty = Item(
        name="Chicken Patty", root=False, identical=True, price=4)
    beef_patty = Item(name="Beef Patty", root=False, identical=True, price=5)
    vegetarian_patty = Item(
        name="Vegetarian Patty", root=False, identical=True, price=3)
    tuna_patty = Item(name="Tuna Patty", root=False, identical=True, price=3)

    db.session.add(chicken_patty)
    db.session.add(beef_patty)
    db.session.add(vegetarian_patty)
    db.session.add(tuna_patty)

    patty_group.options.append(chicken_patty)
    patty_group.options.append(beef_patty)
    patty_group.options.append(vegetarian_patty)
    patty_group.options.append(tuna_patty)

    ingredients = IngredientGroup(
        name="Other Ingredients", max_item=5, max_option=5)
    db.session.add(ingredients)
    main.ingredientgroups.append(ingredients)
    tomato = Item(name="Tomato", root=False, identical=True, price=1)
    tomato_sauce = Item(
        name="Tomato Sauce", root=False, identical=True, price=0.5)
    bbq_sauce = Item(name="BBQ Sauce", root=False, identical=True, price=0.5)
    mint_sauce = Item(name="Mint Sauce", root=False, identical=True, price=0.5)
    chocolate_sauce = Item(
        name="Chocolate Sauce", root=False, identical=True, price=0.5)
    cheddar_cheese = Item(
        name="Cheddar Cheese", root=False, identical=True, price=0.5)
    db.session.add(tomato)
    db.session.add(tomato_sauce)
    db.session.add(bbq_sauce)
    db.session.add(mint_sauce)
    db.session.add(chocolate_sauce)
    db.session.add(cheddar_cheese)

    ingredients.options.append(tomato)
    ingredients.options.append(tomato_sauce)
    ingredients.options.append(bbq_sauce)
    ingredients.options.append(mint_sauce)
    ingredients.options.append(chocolate_sauce)
    ingredients.options.append(cheddar_cheese)
    nuggets = Item(name="Nuggets", root=True, price=2)
    db.session.add(nuggets)
    nuggets_amount = IngredientGroup(
        name="Nuggets Amount",
        max_item=1,
        min_item=1,
        max_option=1,
        min_option=1)

    nuggets.ingredientgroups.append(nuggets_amount)
    nuggets_3_pack = Item(
        name="3-pack Nuggets",
        root=False,
        identical=True,
        price=6,
        stock_unit=3)
    nuggets_6_pack = Item(
        name="6-pack Nuggets",
        root=False,
        identical=True,
        price=12,
        stock_unit=6)
    nuggets_12_pack = Item(
        name="12-pack Nuggets",
        root=False,
        identical=True,
        price=18,
        stock_unit=12)
    db.session.add(nuggets_3_pack)
    db.session.add(nuggets_6_pack)
    db.session.add(nuggets_12_pack)
    nuggets_amount.options.append(nuggets_3_pack)
    nuggets_amount.options.append(nuggets_6_pack)
    nuggets_amount.options.append(nuggets_12_pack)

    fries = Item(name="Fries", root=True, price=2)
    db.session.add(fries)

    fries_size = IngredientGroup(
        name="fries Size", max_item=1, min_item=1, max_option=1, min_option=1)
    db.session.add(fries_size)

    fries.ingredientgroups.append(fries_size)
    small_size = Item(
        name="Small Fries", root=False, identical=True, price=0, stock_unit=150)
    medium_size = Item(
        name="Medium Fries",
        root=False,
        identical=True,
        price=1,
        stock_unit=200)
    large_size = Item(
        name="Large Fries", root=False, identical=True, price=2, stock_unit=250)
    db.session.add(small_size)
    db.session.add(medium_size)
    db.session.add(large_size)

    fries_size.options.append(small_size)
    fries_size.options.append(medium_size)
    fries_size.options.append(large_size)

    sauce = IngredientGroup(name="Sauce", max_item=3, max_option=3)
    db.session.add(sauce)
    nuggets.ingredientgroups.append(sauce)
    fries.ingredientgroups.append(sauce)
    chilli_sauce = Item(
        name="Chilli Sauce", root=False, identical=True, price=1)
    db.session.add(chilli_sauce)

    sauce.options.append(tomato_sauce)
    sauce.options.append(bbq_sauce)
    sauce.options.append(chilli_sauce)
    sauce.options.append(mint_sauce)

    coke = Item(name="Coke", root=True, price=0)
    db.session.add(coke)
    coke_size = IngredientGroup(
        name="Coke Size", max_item=1, min_item=1, max_option=1, min_option=1)
    db.session.add(coke_size)
    coke.ingredientgroups.append(coke_size)
    small_coke = Item(
        name="Small Coke", root=False, identical=True, price=0, stock_unit=150)
    medium_coke = Item(
        name="Medium Coke", root=False, identical=True, price=1, stock_unit=250)
    large_coke = Item(
        name="Large Coke", root=False, identical=True, price=2, stock_unit=350)
    db.session.add(small_coke)
    db.session.add(medium_coke)
    db.session.add(large_coke)

    coke_size.options.append(small_coke)
    coke_size.options.append(medium_coke)
    coke_size.options.append(large_coke)

    sundaes = Item(name="Sundaes", root=True, price=3)
    db.session.add(sundaes)
    sundaes_flavor = IngredientGroup(
        name="Sundaes Flavors",
        max_item=1,
        min_item=1,
        max_option=1,
        min_option=1)
    db.session.add(sundaes)
    sundaes.ingredientgroups.append(sundaes_flavor)
    chocolate_flavor = Item(
        name="Chocolate Sundaes", root=False, identical=True, price=0)
    strawberry_flavor = Item(
        name="Strawberry Sundaes", root=False, identical=True, price=0)

    db.session.add(chocolate_flavor)
    db.session.add(strawberry_flavor)

    sundaes_flavor.options.append(chocolate_flavor)
    sundaes_flavor.options.append(strawberry_flavor)

    sundaes_size = IngredientGroup(
        name="Sundaes Size", max_item=1, min_item=1, max_option=1, min_option=1)

    db.session.add(sundaes_size)
    sundaes.ingredientgroups.append(sundaes_size)

    small_sundaes = Item(
        name="Small Sundaes",
        root=False,
        identical=True,
        price=0,
        stock_unit=100)
    medium_sundaes = Item(
        name="Medium Sundaes",
        root=False,
        identical=True,
        price=1,
        stock_unit=150)
    large_sundaes = Item(
        name="Large Sundaes",
        root=False,
        identical=True,
        price=2,
        stock_unit=200)

    db.session.add(small_sundaes)
    db.session.add(medium_sundaes)
    db.session.add(large_sundaes)

    sundaes_size.options.append(small_sundaes)
    sundaes_size.options.append(medium_sundaes)
    sundaes_size.options.append(large_sundaes)

    db.session.commit()

    # Building the stock
    s_muffin_bun = Stock(name="Muffin Bun", amount=3)
    s_sesame_bun = Stock(name="Sesame Bun", amount=2)
    s_standard_bun = Stock(name="Standard Bun", amount=1000)

    s_wrap = Stock(name="Wrap", amount=1)

    s_chicken_patty = Stock(name="Chicken Patty", amount=10)
    s_beef_patty = Stock(name="Beef Patty", amount=10)
    s_vegetarian_patty = Stock(name="Vegetarian Patty", amount=1)
    s_tuna_patty = Stock(name="Tuna Patty", amount=10)

    s_tomato = Stock(name="Tomato", amount=100)
    s_tomato_sauce = Stock(name="Tomato Sauce", amount=4)
    s_bbq_sauce = Stock(name="BBQ Sauce", amount=10)
    s_mint_sauce = Stock(name="Mint Sauce", amount=100)
    s_chocolate_sauce = Stock(name="Chocolate Sauce", amount=30)
    s_cheddar_cheese = Stock(name="Cheddar Cheese", amount=0)

    s_nuggets = Stock(name="Nuggets", amount=100)

    s_fries = Stock(name="Fries (g)", amount=1000)

    s_coke = Stock(name="Coke (ml)", amount=1000)

    s_sundaes = Stock(name="Sundaes (ml)", amount=1000)

    db.session.add(s_muffin_bun)
    db.session.add(s_sesame_bun)
    db.session.add(s_standard_bun)

    db.session.add(s_wrap)

    db.session.add(s_chicken_patty)
    db.session.add(s_beef_patty)
    db.session.add(s_vegetarian_patty)
    db.session.add(s_tuna_patty)

    db.session.add(s_tomato)
    db.session.add(s_tomato_sauce)
    db.session.add(s_bbq_sauce)
    db.session.add(s_mint_sauce)
    db.session.add(s_chocolate_sauce)
    db.session.add(s_cheddar_cheese)

    db.session.add(s_nuggets)

    db.session.add(s_fries)

    db.session.add(s_coke)

    db.session.add(s_sundaes)

    s_muffin_bun.items.append(muffin_bun)
    s_sesame_bun.items.append(sesame_bun)
    s_standard_bun.items.append(standard_bun)

    s_wrap.items.append(wrap)

    s_chicken_patty.items.append(chicken_patty)
    s_beef_patty.items.append(beef_patty)
    s_vegetarian_patty.items.append(vegetarian_patty)
    s_tuna_patty.items.append(tuna_patty)

    s_tomato.items.append(tomato)
    s_tomato_sauce.items.append(tomato_sauce)
    s_bbq_sauce.items.append(bbq_sauce)
    s_mint_sauce.items.append(mint_sauce)
    s_chocolate_sauce.items.append(chocolate_sauce)
    s_cheddar_cheese.items.append(cheddar_cheese)

    s_nuggets.items.append(nuggets_3_pack)
    s_nuggets.items.append(nuggets_6_pack)
    s_nuggets.items.append(nuggets_12_pack)

    s_fries.items.append(small_size)
    s_fries.items.append(medium_size)
    s_fries.items.append(large_size)

    s_coke.items.append(small_coke)
    s_coke.items.append(medium_coke)
    s_coke.items.append(large_coke)

    s_sundaes.items.append(small_sundaes)
    s_sundaes.items.append(medium_sundaes)
    s_sundaes.items.append(large_sundaes)

    db.session.commit()

    order = Order()

    # Add first main.
    order.AddRootItem(main.GetID(), 1)
    order.AddIG("0.0", [burger.GetID()], [1])
    assert order.GetPrice() == 10

    # There's only 2 sesame bun on stock
    with pytest.raises(RuntimeError):
      order.AddIG("0.0.0.0", [sesame_bun.GetID()], [3])

    order.AddIG("0.0.0.0", [sesame_bun.GetID()], [2])
    assert order.GetPrice() == 14

    order.AddIG("0.1", [chicken_patty.GetID(), beef_patty.GetID()], [2, 1])
    assert order.GetPrice() == 27

    # Unfortunately, cheddar cheese is out of stock
    with pytest.raises(RuntimeError):
      order.AddIG("0.2", [
          tomato.GetID(),
          tomato_sauce.GetID(),
          bbq_sauce.GetID(),
          mint_sauce.GetID(),
          cheddar_cheese.GetID()
      ], [1, 1, 1, 1, 1])
    assert order.GetPrice() == 27

    order.AddIG("0.2", [
        tomato.GetID(),
        tomato_sauce.GetID(),
        bbq_sauce.GetID(),
        mint_sauce.GetID(),
    ], [1, 1, 1, 1])
    assert order.GetPrice() == 29.5

    # Add second main.
    order.AddRootItem(main.GetID(), 1)
    order.AddIG("1.0", [wrap.GetID()], [1])
    assert order.GetPrice() == 34.5

    order.AddIG("1.1", [chicken_patty.GetID()], [3])
    assert order.GetPrice() == 46.5

    order.AddIG("1.2", [tomato.GetID()], [2])
    assert order.GetPrice() == 48.5

    order.AddRootItem(nuggets.GetID(), 1)

    # Buy a 3 pack nuggets
    order.AddIG("2.0", [nuggets_3_pack.GetID()], [1])

    order.AddIG("2.1", [tomato_sauce.GetID()], [0])
    assert order.GetPrice() == 56.5

    order.AddRootItem(nuggets.GetID(), 1)

    # Buy a 6 pack nuggets
    order.AddIG("3.0", [nuggets_6_pack.GetID()], [1])

    order.AddIG("3.1", [tomato_sauce.GetID()], [0])
    assert order.GetPrice() == 70.5

    order.AddRootItem(nuggets.GetID(), 1)

    # Buy a 12 pack nuggets
    order.AddIG("4.0", [nuggets_12_pack.GetID()], [1])

    order.AddIG("4.1", [tomato_sauce.GetID()], [0])
    assert order.GetPrice() == 90.5

    # Buy a small size fries
    order.AddRootItem(fries.GetID(), 1)

    order.AddIG("5.0", [small_size.GetID()], [1])
    assert order.GetPrice() == 92.5

    order.AddIG("5.1", [tomato_sauce.GetID()], [0])
    # Buy a medium size fries
    order.AddRootItem(fries.GetID(), 1)

    order.AddIG("6.0", [medium_size.GetID()], [1])
    assert order.GetPrice() == 95.5

    order.AddIG("6.1", [tomato_sauce.GetID()], [0])

    # Buy a large size fries
    order.AddRootItem(fries.GetID(), 1)

    order.AddIG("7.0", [large_size.GetID()], [1])
    assert order.GetPrice() == 99.5

    order.AddIG("7.1", [tomato_sauce.GetID()], [0])

    # Buy a small coke
    order.AddRootItem(coke.GetID(), 1)

    order.AddIG("8.0", [small_coke.GetID()], [1])
    assert order.GetPrice() == 99.5

    # Buy a medium coke
    order.AddRootItem(coke.GetID(), 1)

    order.AddIG("9.0", [medium_coke.GetID()], [1])
    assert order.GetPrice() == 100.5

    # Buy a large coke
    order.AddRootItem(coke.GetID(), 1)

    order.AddIG("10.0", [large_coke.GetID()], [1])
    assert order.GetPrice() == 102.5

    # Buy a chocolate flavor sundaes
    order.AddRootItem(sundaes.GetID(), 1)

    order.AddIG("11.0", [chocolate_flavor.GetID()], [1])

    order.AddIG("11.1", [small_sundaes.GetID()], [1])
    assert order.GetPrice() == 105.5

    # Buy a strawberry flavor sundaes
    order.AddRootItem(sundaes.GetID(), 1)

    order.AddIG("12.0", [strawberry_flavor.GetID()], [1])

    order.AddIG("12.1", [medium_sundaes.GetID()], [1])
    assert order.GetPrice() == 109.5

    db.session.add(order)
    db.session.commit()

    assert order.GetStatus() == OrderStatus.CREATED

    order.Pay()
    db.session.commit()

    assert s_muffin_bun.GetAmount() == 3
    assert s_sesame_bun.GetAmount() == 0
    assert s_standard_bun.GetAmount() == 1000

    assert s_chicken_patty.GetAmount() == 5
    assert s_beef_patty.GetAmount() == 9
    assert s_vegetarian_patty.GetAmount() == 1
    assert s_tuna_patty.GetAmount() == 10

    assert s_tomato.GetAmount() == 97
    assert s_tomato_sauce.GetAmount() == 3
    assert s_bbq_sauce.GetAmount() == 9
    assert s_mint_sauce.GetAmount() == 99
    assert s_chocolate_sauce.GetAmount() == 30
    assert s_cheddar_cheese.GetAmount() == 0

    assert s_nuggets.GetAmount() == 79

    assert s_fries.GetAmount() == 400

    assert s_coke.GetAmount() == 250

    assert s_sundaes.GetAmount() == 750
    assert order.GetStatus() == OrderStatus.PAID

    assert order.GetPrice() == 109.5


def test_pay_order(app):
  """ Test price are correctly calculated and the order follows business rules.
  """
  with app.app_context():
    main = Item(name="Main", root=True)
    db.session.add(main)

    main_type_group = IngredientGroup(
        name="Main Type", max_item=1, min_item=1, max_option=1, min_option=1)

    main.ingredientgroups.append(main_type_group)
    db.session.add(main_type_group)

    burger = Item(name="Burger", root=False, price=10)
    db.session.add(burger)

    main_type_group.options.append(burger)
    bun_group = IngredientGroup(
        name="Bun", max_item=3, min_item=2, max_option=1, min_option=1)
    db.session.add(bun_group)
    burger.ingredientgroups.append(bun_group)

    muffin_bun = Item(name="Muffin Bun", root=False, identical=True, price=1)
    sesame_bun = Item(name="Sesame Bun", root=False, identical=True, price=2)
    standard_bun = Item(
        name="Standard Bun", root=False, identical=True, price=1)

    db.session.add(muffin_bun)
    db.session.add(sesame_bun)
    db.session.add(standard_bun)

    bun_group.options.append(muffin_bun)
    bun_group.options.append(sesame_bun)
    bun_group.options.append(standard_bun)

    wrap = Item(name="Wrap", root=False, price=5)
    db.session.add(wrap)
    main_type_group.options.append(wrap)

    patty_group = IngredientGroup(
        name="Patties", max_item=3, min_item=1, max_option=3, min_option=1)
    db.session.add(patty_group)
    main.ingredientgroups.append(patty_group)
    chicken_patty = Item(
        name="Chicken Patty", root=False, identical=True, price=4)
    beef_patty = Item(name="Beef Patty", root=False, identical=True, price=5)
    vegetarian_patty = Item(
        name="Vegetarian Patty", root=False, identical=True, price=3)
    tuna_patty = Item(name="Tuna Patty", root=False, identical=True, price=3)

    db.session.add(chicken_patty)
    db.session.add(beef_patty)
    db.session.add(vegetarian_patty)
    db.session.add(tuna_patty)

    patty_group.options.append(chicken_patty)
    patty_group.options.append(beef_patty)
    patty_group.options.append(vegetarian_patty)
    patty_group.options.append(tuna_patty)

    ingredients = IngredientGroup(
        name="Other Ingredients", max_item=5, max_option=5)
    db.session.add(ingredients)
    main.ingredientgroups.append(ingredients)
    tomato = Item(name="Tomato", root=False, identical=True, price=1)
    tomato_sauce = Item(
        name="Tomato Sauce", root=False, identical=True, price=0.5)
    bbq_sauce = Item(name="BBQ Sauce", root=False, identical=True, price=0.5)
    mint_sauce = Item(name="Mint Sauce", root=False, identical=True, price=0.5)
    chocolate_sauce = Item(
        name="Chocolate Sauce", root=False, identical=True, price=0.5)
    cheddar_cheese = Item(
        name="Cheddar Cheese", root=False, identical=True, price=0.5)
    db.session.add(tomato)
    db.session.add(tomato_sauce)
    db.session.add(bbq_sauce)
    db.session.add(mint_sauce)
    db.session.add(chocolate_sauce)
    db.session.add(cheddar_cheese)

    ingredients.options.append(tomato)
    ingredients.options.append(tomato_sauce)
    ingredients.options.append(bbq_sauce)
    ingredients.options.append(mint_sauce)
    ingredients.options.append(chocolate_sauce)
    ingredients.options.append(cheddar_cheese)
    nuggets = Item(name="Nuggets", root=True, price=2)
    db.session.add(nuggets)
    nuggets_amount = IngredientGroup(
        name="Nuggets Amount",
        max_item=1,
        min_item=1,
        max_option=1,
        min_option=1)

    nuggets.ingredientgroups.append(nuggets_amount)
    nuggets_3_pack = Item(
        name="3-pack Nuggets", root=False, identical=True, price=6)
    nuggets_6_pack = Item(
        name="6-pack Nuggets", root=False, identical=True, price=12)
    nuggets_12_pack = Item(
        name="12-pack Nuggets", root=False, identical=True, price=18)
    db.session.add(nuggets_3_pack)
    db.session.add(nuggets_6_pack)
    db.session.add(nuggets_12_pack)
    nuggets_amount.options.append(nuggets_3_pack)
    nuggets_amount.options.append(nuggets_6_pack)
    nuggets_amount.options.append(nuggets_12_pack)

    fries = Item(name="Fries", root=True, price=2)
    db.session.add(fries)

    fries_size = IngredientGroup(
        name="fries Size", max_item=1, min_item=1, max_option=1, min_option=1)
    db.session.add(fries_size)

    fries.ingredientgroups.append(fries_size)
    small_size = Item(name="Small Fries", root=False, identical=True, price=0)
    medium_size = Item(name="Medium Fries", root=False, identical=True, price=1)
    large_size = Item(name="Large Fries", root=False, identical=True, price=2)
    db.session.add(small_size)
    db.session.add(medium_size)
    db.session.add(large_size)

    fries_size.options.append(small_size)
    fries_size.options.append(medium_size)
    fries_size.options.append(large_size)

    sauce = IngredientGroup(name="Sauce", max_item=3, max_option=3)
    db.session.add(sauce)
    nuggets.ingredientgroups.append(sauce)
    fries.ingredientgroups.append(sauce)
    chilli_sauce = Item(
        name="Chilli Sauce", root=False, identical=True, price=1)
    db.session.add(chilli_sauce)

    sauce.options.append(tomato_sauce)
    sauce.options.append(bbq_sauce)
    sauce.options.append(chilli_sauce)
    sauce.options.append(mint_sauce)

    coke = Item(name="Coke", root=True, price=0)
    db.session.add(coke)
    coke_size = IngredientGroup(
        name="Coke Size", max_item=1, min_item=1, max_option=1, min_option=1)
    db.session.add(coke_size)
    coke.ingredientgroups.append(coke_size)
    small_coke = Item(name="Small Coke", root=False, identical=True, price=0)
    medium_coke = Item(name="Medium Coke", root=False, identical=True, price=1)
    large_coke = Item(name="Large Coke", root=False, identical=True, price=2)
    db.session.add(small_coke)
    db.session.add(medium_coke)
    db.session.add(large_coke)
    coke_size.options.append(small_coke)
    coke_size.options.append(medium_coke)
    coke_size.options.append(large_coke)

    sundaes = Item(name="Sundaes", root=True, price=3)
    db.session.add(sundaes)
    sundaes_flavor = IngredientGroup(
        name="Sundaes Flavors",
        max_item=1,
        min_item=1,
        max_option=1,
        min_option=1)
    db.session.add(sundaes)
    sundaes.ingredientgroups.append(sundaes_flavor)
    chocolate_flavor = Item(
        name="Chocolate Sundaes", root=False, identical=True, price=0)
    strawberry_flavor = Item(
        name="Strawberry Sundaes", root=False, identical=True, price=0)

    db.session.add(chocolate_flavor)
    db.session.add(strawberry_flavor)

    sundaes_flavor.options.append(chocolate_flavor)
    sundaes_flavor.options.append(strawberry_flavor)

    sundaes_size = IngredientGroup(
        name="Sundaes Size", max_item=1, min_item=1, max_option=1, min_option=1)

    db.session.add(sundaes_size)
    sundaes.ingredientgroups.append(sundaes_size)

    small_sundaes = Item(
        name="Small Sundaes",
        root=False,
        identical=True,
        price=0,
        stock_unit=100)
    medium_sundaes = Item(
        name="Medium Sundaes",
        root=False,
        identical=True,
        price=1,
        stock_unit=150)
    large_sundaes = Item(
        name="Large Sundaes",
        root=False,
        identical=True,
        price=2,
        stock_unit=200)

    db.session.add(small_sundaes)
    db.session.add(medium_sundaes)
    db.session.add(large_sundaes)

    sundaes_size.options.append(small_sundaes)
    sundaes_size.options.append(medium_sundaes)
    sundaes_size.options.append(large_sundaes)
    db.session.commit()

    order = Order()

    # Add first main.
    order.AddRootItem(main.GetID(), 1)
    order.AddIG("0.0", [burger.GetID()], [1])
    assert order.GetPrice() == 10

    # Can't complete the order without choosing at least one bun.
    with pytest.raises(RuntimeError):
      order.Pay()

    # Customer can't order less than 1 bun or more than 3 buns.
    with pytest.raises(ValueError):
      order.AddIG("0.0.0.0", [muffin_bun.GetID()], [1])

    with pytest.raises(ValueError):
      order.AddIG("0.0.0.0", [muffin_bun.GetID()], [4])

    order.AddIG("0.0.0.0", [muffin_bun.GetID()], [2])
    assert order.GetPrice() == 12

    # Can't complete the order without choosing at least one patty.
    with pytest.raises(RuntimeError):
      order.Pay()

    # Can't choose more than three types of patties.
    with pytest.raises(ValueError):
      order.AddIG("0.1", [
          chicken_patty.GetID(),
          beef_patty.GetID(),
          vegetarian_patty.GetID(),
          tuna_patty.GetID()
      ], [1, 1, 1, 1])

    # Can't choose more than three patties.
    with pytest.raises(ValueError):
      order.AddIG(
          "0.1",
          [chicken_patty.GetID(),
           beef_patty.GetID(),
           vegetarian_patty.GetID()], [1, 1, 2])

    # Customer can't choose zero patties or more than 4 patties.
    with pytest.raises(ValueError):
      order.AddIG("0.1", [chicken_patty.GetID()], [0])

    with pytest.raises(ValueError):
      order.AddIG("0.1", [chicken_patty.GetID()], [4])

    order.AddIG("0.1", [chicken_patty.GetID()], [3])

    assert order.GetPrice() == 24

    # Patty has been fulfilled so RuntimeError is raised.
    with pytest.raises(RuntimeError):
      order.AddIG("0.1", [beef_patty.GetID()], [3])

    # Can't choose more than five types of ingredients.
    with pytest.raises(ValueError):
      order.AddIG("0.2", [
          tomato.GetID(),
          tomato_sauce.GetID(),
          bbq_sauce.GetID(),
          mint_sauce.GetID(),
          chocolate_sauce.GetID(),
          cheddar_cheese.GetID()
      ], [1, 1, 1, 1, 1, 1])

    # Can't choose more than five ingredients with more than one ingredient.
    with pytest.raises(ValueError):
      order.AddIG("0.2", [
          tomato.GetID(),
          tomato_sauce.GetID(),
          bbq_sauce.GetID(),
          mint_sauce.GetID(),
          cheddar_cheese.GetID()
      ], [1, 1, 2, 1, 1])

    # Can't choose more than five ingredients with one ingredient.
    with pytest.raises(ValueError):
      order.AddIG("0.2", [tomato.GetID()], [6])

    order.AddIG("0.2", [
        tomato.GetID(),
        tomato_sauce.GetID(),
        bbq_sauce.GetID(),
        mint_sauce.GetID(),
        cheddar_cheese.GetID()
    ], [1, 1, 1, 1, 1])
    assert order.GetPrice() == 27

    # Add second main.
    order.AddRootItem(main.GetID(), 1)
    order.AddIG("1.0", [wrap.GetID()], [1])
    assert order.GetPrice() == 32

    order.AddIG("1.1", [chicken_patty.GetID()], [3])
    assert order.GetPrice() == 44

    order.AddIG("1.2", [tomato.GetID()], [2])
    assert order.GetPrice() == 46

    order.AddRootItem(nuggets.GetID(), 1)

    # Can't choose more than one nuggets pack.
    with pytest.raises(ValueError):
      order.AddIG("2.0", [nuggets_3_pack.GetID()], [2])

    # Can't choose more than one type of nuggets pack.
    with pytest.raises(ValueError):
      order.AddIG("2.0", [nuggets_3_pack.GetID(),
                          nuggets_3_pack.GetID()], [1, 1])

    order.AddIG("2.0", [nuggets_3_pack.GetID()], [1])

    # Can't pay before configure any sauces for nuggets.
    with pytest.raises(RuntimeError):
      order.Pay()

    # Can't choose more than three sauces.
    with pytest.raises(ValueError):
      order.AddIG("2.1", [tomato_sauce.GetID()], [4])

    # Can't choose more than three types of sauces.
    with pytest.raises(ValueError):
      order.AddIG("2.1", [
          tomato_sauce.GetID(),
          bbq_sauce.GetID(),
          chilli_sauce.GetID(),
          mint_sauce.GetID()
      ], [1, 1, 1, 1])

    order.AddIG("2.1", [tomato_sauce.GetID()], [0])
    assert order.GetPrice() == 54

    order.AddRootItem(fries.GetID(), 1)

    # Can't pay without choosing a pack of fries.
    with pytest.raises(RuntimeError):
      order.Pay()

    # Can't choose more than one pack of fries.
    with pytest.raises(ValueError):
      order.AddIG("3.0", [small_size.GetID()], [2])

    # Can't choose more than one type of fries.
    with pytest.raises(ValueError):
      order.AddIG("3.0", [small_size.GetID(), medium_size.GetID()], [1, 1])

    order.AddIG("3.0", [small_size.GetID()], [1])
    assert order.GetPrice() == 56

    # Can't pay without choosing any sauces.
    with pytest.raises(RuntimeError):
      order.Pay()

    # Can't choose more than three sauces.
    with pytest.raises(ValueError):
      order.AddIG("3.1", [tomato_sauce.GetID()], [4])

    # Can't choose more than three types of sauces.
    with pytest.raises(ValueError):
      order.AddIG("3.1", [
          tomato_sauce.GetID(),
          bbq_sauce.GetID(),
          chilli_sauce.GetID(),
          mint_sauce.GetID()
      ], [1, 1, 1, 1])

    order.AddIG("3.1", [tomato_sauce.GetID()], [0])

    order.AddRootItem(coke.GetID(), 1)

    # Can't pay without choosing a coke.
    with pytest.raises(RuntimeError):
      order.Pay()

    # Can't choose more than one coke.
    with pytest.raises(ValueError):
      order.AddIG("4.0", [small_coke.GetID()], [2])

    # Can't choose more than one type of coke.
    with pytest.raises(ValueError):
      order.AddIG("4.0", [small_coke.GetID(), medium_coke.GetID()], [1, 1])

    order.AddIG("4.0", [medium_coke.GetID()], [1])
    assert order.GetPrice() == 57

    # Buy a chocolate flavor sundaes
    order.AddRootItem(sundaes.GetID(), 1)

    order.AddIG("5.0", [chocolate_flavor.GetID()], [1])

    with pytest.raises(RuntimeError):
      order.AddIG("5.0", [strawberry_flavor.GetID()], [1])

    order.AddIG("5.1", [small_sundaes.GetID()], [1])

    with pytest.raises(RuntimeError):
      order.AddIG("5.1", [large_sundaes.GetID()], [1])

    assert order.GetPrice() == 60

    # Buy a strawberry flavor sundaes
    order.AddRootItem(sundaes.GetID(), 1)

    order.AddIG("6.0", [strawberry_flavor.GetID()], [1])

    with pytest.raises(RuntimeError):
      order.AddIG("6.0", [chocolate_flavor.GetID()], [1])

    order.AddIG("6.1", [medium_sundaes.GetID()], [1])

    with pytest.raises(RuntimeError):
      order.AddIG("6.1", [large_sundaes.GetID()], [1])

    assert order.GetPrice() == 64

    db.session.add(order)
    db.session.commit()

    assert order.GetStatus() == OrderStatus.CREATED

    order.Pay()
    db.session.commit()

    assert order.GetStatus() == OrderStatus.PAID
    assert order.GetPrice() == 64


def test_index(client, app):
  """ Test customer index page
  """
  with app.app_context():
    response = client.get('/')
    assert b"Welcome!" in response.data
    user = User(
        name="Jeff", email="jeff@google.com", user_type=UserType.CUSTOMER)
    user.SetPassword("123456")
    db.session.add(user)
    db.session.commit()
    login(client, "jeff@google.com", "123456")
    response = client.get('/')
    assert b"Welcome, Jeff" in response.data


def test_order_details(client, app):
  """ Test correct order details on front end
  """
  with app.app_context():
    sburger = Stock(name="burger", amount=10)
    swrap = Stock(name="wrap", amount=10)
    db.session.add(sburger)
    db.session.add(swrap)
    imain = Item(name="main")
    iburger = Item(name="burger")
    iwrap = Item(name="wrap")
    gtype = IngredientGroup(
        name="type", min_item=1, max_item=1, min_option=1, max_option=1)
    db.session.add(imain)
    db.session.add(iburger)
    db.session.add(iwrap)
    db.session.add(gtype)
    sburger.items.append(iburger)
    swrap.items.append(iwrap)
    gtype.options.append(iburger)
    gtype.options.append(iwrap)
    imain.ingredientgroups.append(gtype)
    db.session.commit()

    user = User(
        name="Dickson", email="dickon@gmail.com", user_type=UserType.ADMIN)
    user.SetPassword("123456")
    user1 = User(name="123", email="123@gmail.com", user_type=UserType.CUSTOMER)
    user1.SetPassword("123456")
    user2 = User(
        name="Superman",
        email="Superman@gmail.com",
        user_type=UserType.CUSTOMER)
    user2.SetPassword("123456")

    order = Order(status=OrderStatus.PAID, price=100)
    user2.orders.append(order)
    order.AddRootItem(imain.GetID(), 1)
    order.AddIG("0.0", [iburger.GetID()], [1])

    db.session.add(user)
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(order)
    db.session.commit()

    login(client, "Superman@gmail.com", "654321")
    response = client.get('/order/%d' % order.GetID())
    assert response.status == '302 FOUND'

    login(client, "dickon@gmail.com", "123456")
    response = client.get('/order/%d' % order.GetID())
    assert b"Superman" in response.data
    assert order.GetDetailsString().encode("utf-8") in response.data
    if order.GetStatusText() != "ready":
      assert b"Mark as done" in response.data

    login(client, "123@gmail.com", "123456")
    response = client.get('/order/%d' % order.GetID())
    assert response.status == '302 FOUND'

    login(client, "Superman@gmail.com", "123456")
    response = client.get('/order/%d' % order.GetID())
    assert b"Superman" in response.data

    # Check if the user can see his unique order ID in the details page.
    assert "ORDER {0}".format(order.GetID()).encode("utf-8") in response.data

    # Customer shouldn't have access to details page of unpaid orders
    order.SetStatus(OrderStatus.CREATED)
    db.session.commit()
    response = client.get('/order/%d' % order.GetID())
    assert response.status == '302 FOUND'


def test_checkout_page(client, app):
  """ Test checkout page is valid
  """
  with app.app_context():
    sburger = Stock(name="burger", amount=10)
    swrap = Stock(name="wrap", amount=10)
    db.session.add(sburger)
    db.session.add(swrap)
    imain = Item(name="main")
    iburger = Item(name="burger")
    iwrap = Item(name="wrap")
    gtype = IngredientGroup(
        name="type", min_item=1, max_item=1, min_option=1, max_option=1)
    db.session.add(imain)
    db.session.add(iburger)
    db.session.add(iwrap)
    db.session.add(gtype)
    sburger.items.append(iburger)
    swrap.items.append(iwrap)
    gtype.options.append(iburger)
    gtype.options.append(iwrap)
    imain.ingredientgroups.append(gtype)
    db.session.commit()
    user = User(
        name="Dickson", email="dickon@gmail.com", user_type=UserType.ADMIN)
    user.SetPassword("123456")
    user2 = User(
        name="Superman",
        email="Superman@gmail.com",
        user_type=UserType.CUSTOMER)
    user2.SetPassword("123456")
    order = Order(status=OrderStatus.PAID, price=100)
    user2.orders.append(order)
    order.AddRootItem(imain.GetID(), 1)
    order.AddIG("0.0", [iburger.GetID()], [1])
    db.session.add(user)
    db.session.add(user2)
    db.session.add(order)
    db.session.commit()
    login(client, "dickon@gmail.com", "123456")
    order = Order.query.get(order.GetID())
    response = client.get('/order/%d' % order.GetID())
    # Check if the customer can see the unique ID for the order.
    assert str(order.GetID()).encode("utf-8") in response.data
    client.get('/admin/order/%d/done' % order.GetID())
    # Check if the customer can see the details of his order.
    assert order.GetDetailsString().encode("utf-8") in response.data
