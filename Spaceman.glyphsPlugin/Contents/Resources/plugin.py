# encoding: utf-8

from GlyphsApp.plugins import *
from Foundation import *
from AppKit import *

from SpaceSolver import SpaceSolver

dirtyHack = None
class SpacemanView(NSView):
  scalefactor = 5.0/72.0
  selectedIdx = None
  dragDir = None

  def drawRect_(self, dirtyRect):
    global dirtyHack
    NSColor.whiteColor().setFill();
    NSRectFill(dirtyRect)
    if not (dirtyHack and Glyphs.font and Glyphs.font.selectedFontMaster):
      return

    try:
      gc = NSGraphicsContext.currentContext()
      gc.saveGraphicsState()
      NSColor.blackColor().setStroke()
      for idx,l,rect,dist in self.textIterator():
        if idx == self.selectedIdx:
          NSColor.redColor().setFill()
        else:
          NSColor.blackColor().setFill()
        self.drawGSLayer_atX_atY_(l,rect.origin.x,rect.origin.y)
      gc.restoreGraphicsState()
    except:
      NSLog(traceback.format_exc())

  def textIterator(self):
    global dirtyHack
    try:
      x = 0
      layerHeight = -Glyphs.font.selectedFontMaster.descender + Glyphs.font.selectedFontMaster.ascender
      y = self.bounds().size.height - self.scalefactor*layerHeight
      s = self.scalefactor
      layerHeight = -Glyphs.font.selectedFontMaster.descender + Glyphs.font.selectedFontMaster.ascender
      idx = 0
      lastChar = None
      lastRSB = 0
      for char in dirtyHack.smTextarea.stringValue().decode("utf-8"):
        # XXX This won't work when glyph name != character (eg á != aacute)
        if char == " ":
          char = "space"
          if x == 0:
            continue
        l = Glyphs.font.glyphs[char].layers[Glyphs.font.selectedFontMaster.id]
        kern = 0
        if lastChar:
          kern = Glyph.font.kerningForPair(Glyphs.font.selectedFontMaster.id,lastChar,char)
          if kern > 10000:
            kern = 0
          x += kern * s
        if x + l.width * s > self.bounds().size.width:
          y -= layerHeight * s
          x = 0
        rect = NSMakeRect(x,y,l.width*s,layerHeight * s)
        dist = lastRSB + l.LSB + kern
        lastRSB = l.RSB
        yield idx,l,rect,dist
        idx += 1
        x += l.width * s
    except:
      NSLog(traceback.format_exc())

  def drawGSLayer_atX_atY_(self,l,x,y):
    try:
      transform = NSAffineTransform.transform();
      transform.translateXBy_yBy_(x,y)
      transform.scaleBy_(self.scalefactor)
      GlyphBezierPath = l.bezierPath or NSBezierPath.alloc().init()
      GlyphBezierPath = GlyphBezierPath.copy()
      OpenGlyphsPath = l.openBezierPath or NSBezierPath.alloc().init()
      OpenGlyphsPath = OpenGlyphsPath.copy()
      for currComponent in l.components:
        GlyphBezierPath.appendBezierPath_(currComponent.bezierPath.copy())
        OpenGlyphsPath.appendBezierPath_(currComponent.openBezierPath.copy())
      GlyphBezierPath.transformUsingAffineTransform_(transform)
      OpenGlyphsPath.transformUsingAffineTransform_(transform)
      GlyphBezierPath.fill()
      OpenGlyphsPath.setLineWidth_(0.75)
      OpenGlyphsPath.stroke()
    except:
      NSLog(traceback.format_exc())

  def mouseDown_(self, theEvent):
    loc = self.convertPoint_fromView_(theEvent.locationInWindow(),None)
    for idx,l,rect,dist in self.textIterator():
      if NSPointInRect(loc, rect):
        self.selectedIdx = idx
        self.setNeedsDisplay_(True)

  def mouseUp_(self, theEvent):
    self.dragDir = None

  def mouseDragged_(self, theEvent):
    try:
      if not(self.selectedIdx) or self.selectedIdx < 1:
        return
      delta = theEvent.deltaX() / self.scalefactor
      print("Delta was %.f" % delta)
      if abs(delta) <= 1:
        return
      if not self.dragDir:
        self.dragDir = delta / abs(delta)
      self.prepSolver()
      for idx,l,rect,dist in self.textIterator():
        if idx == self.selectedIdx:
          self.solver.modify(lastL,l,dist+delta)
        lastL = l
      result = self.solver.solve()
      self.solver.setResult(result)
      self.setNeedsDisplay_(True)
    except:
      NSLog(traceback.format_exc())

  def prepSolver(self):
    lastL = None
    self.solver = SpaceSolver()
    for idx,l,rect,dist in self.textIterator():
      if l and lastL:
        self.solver.prepare(lastL, l)
      lastL = l
    self.solver.addKernConstraint("n","n")
    self.solver.addKernConstraint("o","o")
    self.solver.addKernConstraint("o","n")
    self.solver.addKernConstraint("n","o")
    self.solver.addBalanceConstraint("o")

class Spaceman(GeneralPlugin):
  spacemanWindow = objc.IBOutlet()
  smTextarea = objc.IBOutlet()
  smConstraintlist = objc.IBOutlet()
  smCancelbutton = objc.IBOutlet()
  smOkbutton = objc.IBOutlet()
  smView = objc.IBOutlet()

  def start(self):
    try:
      global dirtyHack
      self.name = "Spaceman"
      dirtyHack = self
      NSBundle.loadNibNamed_owner_( "SpacemanWindow", self )
      print(self.smTextarea)
      mainMenu = NSApplication.sharedApplication().mainMenu()
      glyphMenu = mainMenu.itemWithTag_(7).submenu()
      s = objc.selector(self.launchSpaceman, signature='v@:')
      newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Spaceman", s, "")
      newMenuItem.setTarget_(self)
      glyphMenu.addItem_(newMenuItem)
    except:
      NSLog(traceback.format_exc())

  def launchSpaceman(self):
    try:
      self.spacemanWindow.makeKeyAndOrderFront_(self)
    except:
      NSLog(traceback.format_exc())

  @objc.IBAction
  def viewKeyDown_(self, theEvent):
    pass

  @objc.IBAction
  def viewMouseDragged_(self, theEvent):
    print("drag")

  @objc.IBAction
  def okClicked_(self, sender):
    pass

  @objc.IBAction
  def cancelClicked_(self, sender):
    pass

  def controlTextDidChange_(self, notification):
    try:
      self.smView.setNeedsDisplay_(True)
    except:
      NSLog(traceback.format_exc())

  def __file__(self):
    """Please leave this method unchanged"""
    return __file__
  
