
import cocos
import math


class OurSprite(cocos.sprite.Sprite):
    def moveTo(self, position):
        self.position = position

    def moveBy(self, adjustment):
        # add the adjustment coordinates to the current position
        self.position = map(sum, zip(self.position, adjustment))

    # move along the local X axis
    def moveForward(self, doForward, rotation = None, doReturn = False):
        if rotation == None:
            rotation = self.rotation

        doX = doForward * math.cos(math.radians(rotation))
        doY = doForward * -math.sin(math.radians(rotation))
        self.moveBy((doX, doY))

        if doReturn:
            return doX, doY

    # move along the local Y axis
    def moveUpward(self, doUpward):
        doX = doUpward * math.cos(math.radians(self.rotation - 90))
        doY = doUpward * -math.sin(math.radians(self.rotation - 90))
        self.moveBy((doX, doY))

    def rotateBy(self, adjustment):
        self.rotation += adjustment

    def rotateTo(self, rotation):
        self.rotation = rotation

    def cleanRot(self, rotation):
        while rotation > 360:
            rotation -= 360

        while rotation < -360:
            rotation += 360

        return rotation
