"""Test ES2: As a staff member, I'd like to view and update orders."""

from app.core.models.order import Order, OrderStatus
from app.core.models import db
from app.core.models.user import User, UserType
from app.core.models.inventory import Stock, Item, IngredientGroup


def login(client, email, password):
  return client.post(
      '/accounts/signin',
      data={
          "email": email,
          "password": password
      },
      follow_redirects=True)


def test_order_list(client, app):
  """test order list page"""
  with app.app_context():
    order = Order(price=123, status=OrderStatus.PAID)
    db.session.add(order)
    db.session.commit()
    timestamp = order.GetCreatedAt()
    user = User(
        name="Dickson", email="dickon@gmail.com", user_type=UserType.ADMIN)
    user.SetPassword("123456")
    db.session.add(user)
    db.session.commit()
    login(client, "dickon@gmail.com", "123456")

  response = client.get('/admin/orderlist')
  rsp = str(response.data)
  assert "ID" in rsp
  assert "User Name" in rsp
  assert "Price" in rsp
  assert "Created at" in rsp
  assert "Updated at" in rsp
  assert "Status" in rsp
  assert "123" in rsp
  assert "paid" in rsp
  assert str(timestamp) in rsp

  with app.app_context():
    order1 = Order(price=231, status=OrderStatus.PAID)
    db.session.add(order1)
    db.session.commit()

  response = client.get('/admin/orderlist')
  rsp = str(response.data)
  assert "231" in rsp
  position = rsp.find("123")
  position1 = rsp.find("231")
  assert position1 < position


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


def test_mark_as_done(client, app):
  """test mark done page"""
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
    assert b"paid" in response.data

    client.get('/admin/order/%d/done' % order.GetID())
    response = client.get('/order/%d' % order.GetID())
    assert b"ready" in response.data
