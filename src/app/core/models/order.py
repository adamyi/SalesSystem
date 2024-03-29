"""Order module"""

from datetime import datetime
import enum
from functools import reduce
import json
from app.core.models.inventory import Item, IngredientGroup
from . import db


class OrderStatus(enum.Enum):
  CREATED = 0
  PAID = 1
  READY = 2


class Order(db.Model):
  """Order class"""
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  status = db.Column(db.Enum(OrderStatus), default=OrderStatus.CREATED)
  price = db.Column(db.Float, default=0)
  created_at = db.Column(db.DateTime, default=datetime.now)
  updated_at = db.Column(
      db.DateTime, default=datetime.now, onupdate=datetime.now)
  content = db.Column(db.Text, default="[]")

  def GetID(self):
    return self.id

  def GetUserID(self):
    return self.user_id

  def GetStatus(self):
    return self.status

  def GetStatusText(self):
    return self.status.name.lower()

  def GetPrice(self):
    return self.price

  def GetCreatedAt(self):
    return self.created_at

  def GetUpdatedAt(self):
    return self.updated_at

  def GetContent(self):
    return self.content

  def SetID(self, oid):
    self.id = oid

  def SetStatus(self, status):
    self.status = status

  def AddIG(self, path, items, numbers):
    """fulfill an ingredient group of an existing item in the order"""
    content = json.loads(self.content)
    fids = path.split('.')
    root_id = int(fids[0])
    node = ItemNode.FromDict(content[root_id])
    content[root_id] = node
    coefficient = 1
    for fid in fids[1:]:
      if node.type == "item":
        coefficient *= node.num
      node = node.GetChild(int(fid))
    self.price += node.SetItems(items, numbers, coefficient)
    self.content = json.dumps(content)

  def AddRootItem(self, item_id, num):
    """add a new root item to the order"""
    item = Item.query.get(item_id)
    if item is None:
      raise ValueError('Item doesn\'t exist!' % item_id)
    if not item.HasEnoughStock(num):
      raise RuntimeError('We don\'t have enough stock for %s' % item.GetName())
    if self.content is None:
      content = []
    else:
      content = json.loads(self.content)
    if self.price is None:
      self.price = 0
    if item.CanShareIdenticalIG():
      node = ItemNode.FromItem(item, num)
      self.price += node.price
      content.append(node)
    else:
      for _ in range(num):
        node = ItemNode.FromItem(item, 1)
        self.price += node.price
        content.append(node)
    self.content = json.dumps(content)

  def GetDetailsString(self):
    """Return the details string of the order.
    """
    content = json.loads(self.content)
    details = ""
    for item in content:
      details += ItemNode.FromDict(item).GetDetailsString()
    if self.price is None:
      self.price = 0
    details += "\n\nTotal price: $%.2f" % self.price
    return details

  def GetUnfulfilledIGDetails(self):
    content = json.loads(self.content)
    for idx, item in enumerate(content):
      ret = ItemNode.FromDict(item).GetUnfulfilledIGDetails(
          str(idx), item["name"])
      if ret is not None:
        return ret
    return None

  def DeductStock(self):
    content = json.loads(self.content)
    for item in content:
      ItemNode.FromDict(item).DeductStock()

  def Pay(self):
    if self.GetUnfulfilledIGDetails() is not None:
      raise RuntimeError("Ingredient group configuration is not complete")
    content = json.loads(self.content)
    for item in content:
      ItemNode.FromDict(item).DeductStock()
    self.status = OrderStatus.PAID


class OrderNode(dict):
  """A node structure in order content"""

  def __init__(self, Type, Id, name):
    super().__init__()
    self.__dict__ = self
    self.name = name
    self.id = Id
    self.type = Type
    self.children = []

  def AddChild(self, child):
    self.children.append(child)

  def GetChildren(self):
    return self.children

  def GetChild(self, idx):
    return self.children[idx]

  def GetName(self):
    return self.name

  def GetID(self):
    return self.id

  def GetType(self):
    return self.type

  def GetUnfulfilledIGDetails(self, path, item_name):
    for idx, child in enumerate(self.children):
      if self.type == "item":
        item_name = self.name
      ret = child.GetUnfulfilledIGDetails(path + ".%d" % idx, item_name)
      if ret is not None:
        return ret
    return None


class ItemNode(OrderNode):
  """A node structure representing an item in order content"""

  @staticmethod
  def FromDict(dict_):
    """ Recursively (re)construct ItemNode-based tree from dictionary. """
    root = ItemNode(dict_['id'], dict_['name'], dict_['num'], dict_['price'])
    root.children = list(map(IGNode.FromDict, dict_['children']))
    return root

  @staticmethod
  def FromItem(item, number, coefficient=1):
    if item.GetMaxItem() is not None and number > item.GetMaxItem():
      raise ValueError(
          'Number of %s can\'t exceed %d' % (item.name, item.max_item))
    ret = ItemNode(item.GetID(), item.GetName(), number,
                   item.GetPrice() * number * coefficient)
    for ig in item.ingredientgroups:
      ret.AddChild(IGNode.FromIG(ig))
    return ret

  def __init__(self, Id, name, num, price):
    super().__init__("item", Id, name)
    self.num = num
    self.price = price

  def GetNum(self):
    return self.num

  def GetPrice(self):
    return self.price

  def GetDetailsString(self, prefix=""):
    """Recursively get the details string for an order item node
    for invoice and order details"""
    ret = "%s%s%s%s\n" % (
        prefix, self.name, "*%d" % self.num if self.num > 1 else "",
        " ......$%.2f" % self.price if self.price != 0 else "")

    prefix = (len(prefix) - len(prefix.lstrip()) + 2) * " "
    for child in self.children:
      ret += child.GetDetailsString(prefix)
    return ret

  def DeductStock(self, coefficient=1):
    item = Item.query.get(self.id)
    try:
      if item.stock is not None:
        item.stock.DecreaseAmount(item.stock_unit * self.num * coefficient)
    except RuntimeError:
      raise RuntimeError("Stock not enough for %s" % self.name)
    coefficient *= self.num
    for child in self.children:
      child.DeductStock(coefficient)


class IGNode(OrderNode):
  """A node structure representing an ig in order content"""

  @staticmethod
  def FromDict(dict_):
    """ Recursively (re)construct IGNode-based tree from dictionary. """
    root = IGNode(dict_['id'], dict_['name'])
    if dict_['fulfilled']:
      root.SetFulfilled()
    root.children = list(map(ItemNode.FromDict, dict_['children']))
    return root

  @staticmethod
  def FromIG(ig):
    return IGNode(ig.GetID(), ig.GetName())

  def __init__(self, Id, name):
    super().__init__("ig", Id, name)
    self.fulfilled = False

  def IsFulfilled(self):
    return self.fulfilled

  def SetFulfilled(self, ig=None):
    """Check whether an order node fulfills all requirements
    for this ingredient group and then mark it as fulfilled"""
    if ig is not None:
      options = len({x.id for x in self.children if x.num > 0})
      items = reduce((lambda x, y: x + y.num), self.children, 0)
      if ig.GetMinOption() is not None and options < ig.GetMinOption():
        raise ValueError(
            "At least %d different offerings must be selected from %s" %
            (ig.GetMinOption(), self.name))
      if ig.GetMaxOption() is not None and options > ig.GetMaxOption():
        raise ValueError(
            "At most %d different offerings can be selected from %s" %
            (ig.GetMaxOption(), self.name))
      if ig.GetMinItem() is not None and items < ig.GetMinItem():
        raise ValueError("At least %d items must be chosen in %s" %
                         (ig.GetMinItem(), self.name))
      if ig.GetMaxItem() is not None and items > ig.GetMaxItem():
        raise ValueError("At most %d items can be chosen in %s" %
                         (ig.GetMaxItem(), self.name))
    self.fulfilled = True

  def SetItems(self, items, numbers, coefficient=1):
    """Set customer's choice for items within this ig in an order
    Returns added price
    """

    price = 0
    if self.fulfilled:
      raise RuntimeError('Cannot fulfill %s twice' % self.name)
    ig = IngredientGroup.query.get(self.id)
    if ig is None:
      raise ValueError('Cannot find IngredientGroup')
    for i, item_id in enumerate(items):
      if numbers[i] <= 0:
        continue
      item = Item.query.get(item_id)
      if item is None:
        raise ValueError('Item doesn\'t exist!' % item_id)
      if not item.HasEnoughStock(numbers[i] * coefficient):
        raise RuntimeError(
            'We don\'t have enough stock for %s' % item.GetName())
      if item.CanShareIdenticalIG():
        node = ItemNode.FromItem(item, numbers[i], coefficient)
        price += node.price
        self.AddChild(node)
      else:
        for _ in range(numbers[i]):
          node = ItemNode.FromItem(item, 1, coefficient)
          price += node.price
          self.AddChild(node)
    self.SetFulfilled(ig)
    return price

  def GetDetailsString(self, prefix=""):
    """Recursively get the details string for an order ig node
    for invoice and order details"""
    ret = ""
    prefix += self.name + ":"
    for child in self.children:
      ret += child.GetDetailsString(prefix)
    return ret

  def GetUnfulfilledIGDetails(self, path, item_name):
    if not self.fulfilled:
      return {"path": path, "item_name": item_name, "id": self.id}
    return super().GetUnfulfilledIGDetails(path, item_name)

  def DeductStock(self, coefficient):
    for child in self.children:
      child.DeductStock(coefficient)
