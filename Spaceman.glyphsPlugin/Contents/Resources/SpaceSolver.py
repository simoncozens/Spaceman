import nlopt
from GlyphsApp.plugins import *

class SpaceSolver:
  def __init__(self):
    self.var = {}
    self.x = []
    self.constraints = {}

  def assignVariable(self, name, guess):
    if name in self.var:
      return self.var[name]
    else:
      self.var[name] = len(self.var)
      if self.var[name] >= len(self.x):
        self.x.extend(0 for _ in range(len(self.x), self.var[name] + 1))
      self.x[self.var[name]] = guess

      return self.var[name]

  def kernCost(self, x, grad):
      cost = 0.0
      for k in self.var.keys():
        if k.startswith("kern"):
          cost += self.x[self.var[k]] ** 2
      return cost

  def addConstraint(self,l,r,d,guess=50):
    rsb = self.assignVariable("RSB|"+l, guess)
    lsb = self.assignVariable("LSB|"+r, guess)
    kern = self.assignVariable("kern|"+l+"|"+r, 0)
    self.constraints[l+r] = lambda: self.opt.add_equality_constraint(lambda x,grad: x[rsb] + x[lsb] + x[kern] - d)

  def addKernConstraint(self,l,r):
    kern = self.assignVariable("kern|"+l+"|"+r, 0)
    self.constraints["zerokern"+l+r] = lambda: self.opt.add_equality_constraint(lambda x,grad: x[kern])

  def addBalanceConstraint(self,l,guess=50):
    rsb = self.assignVariable("RSB|"+l, guess)
    lsb = self.assignVariable("LSB|"+l, guess)
    self.constraints["balance"+l] = lambda: self.opt.add_equality_constraint(lambda x,grad: x[rsb] - x[lsb])

  def solve(self):
    self.opt = nlopt.opt(nlopt.LN_COBYLA,len(self.x))
    self.opt.set_min_objective(lambda x,grad: self.kernCost(x,grad))
    self.opt.set_xtol_rel(0.0001)
    for k in self.constraints: self.constraints[k]()
    x = self.opt.optimize(self.x)
    return {k: x[self.var[k]] for k in self.var}

  def prepare(self,left,right):
    l = left.parent.name
    r = right.parent.name
    kern = Glyphs.font.kerningForPair(Glyphs.font.selectedFontMaster.id,l,r)
    if kern > 10000:
      kern = 0
    d = left.RSB + right.LSB + kern
    self.addConstraint(l,r,d, guess = d/2)

  def modify(self,left,right,d):
    l = left.parent.name
    r = right.parent.name
    self.addConstraint(l,r,d, guess = d/2)

  def setResult(self,result):
    for key in result:
      if key.startswith("LSB|"):
        char = key[4:]
        g = Glyphs.font.glyphs[char].layers[Glyphs.font.selectedFontMaster.id]
        g.LSB = result[key]
      if key.startswith("RSB|"):
        char = key[4:]
        g = Glyphs.font.glyphs[char].layers[Glyphs.font.selectedFontMaster.id]
        g.RSB = result[key]
      if key.startswith("kern|"):
        k,l,r = key.split("|")
        Glyphs.font.setKerningForPair(Glyphs.font.selectedFontMaster.id,l,r,result[key])
