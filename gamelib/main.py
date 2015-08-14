# entry point from `run_game.py`

from cocos import collision_model
from cocos.director import director

import cocos
import copy
import pyglet
import random
import sys
import time

# my modules
from sprite import OurSprite

import config
import data
import scenes


def checkMap(sprite, mapCollider, map, deltaTime = None):
    last = sprite.get_rect()
    new = last.copy()
    new.x += sprite.doX
    new.y += sprite.doY
    mapCollider.collide_map(map, last, new, sprite.doY, sprite.doX)

    if deltaTime:
        sprite.update(deltaTime)

    else:
        sprite.update()


class MainGameLayer(cocos.layer.ScrollableLayer):

    is_event_handler = True

    def __init__(self, sceneManager):
        super(MainGameLayer, self).__init__()
        self.sceneManager = sceneManager

        self.freeze = False

        self.keysPressed = set()

        self.schedule(self.update)


        self.player = Player((200, 500))
        self.add(self.player)
        self.playerMapCollider = PlayerMapCollider(self.player)

        self.badputer = Badputer((550, 200), (500, 700))
        self.add(self.badputer)
        self.enemies = set()
        self.enemies.add(self.badputer)

        self.collisionManager = collision_model.CollisionManagerBruteForce()

        self.bullet = None
        self.bulletStuff = set()
        self.bulletMap = cocos.tiles.load(data.getPath("bullet_map.tmx"))["Tile Layer 1"]
        self.bulletMapCollider = None

        self.tempAnimations = set()

    def update(self, deltaTime):
        keyNames = [pyglet.window.key.symbol_string(k) for k in self.keysPressed]

        ######################################################

        if "W" in keyNames:
            if self.freeze:
                # navigate bullet
                if self.bullet.DIRECTION == "right":
                    self.bullet.rotation -= 2.5

                elif self.bullet.DIRECTION == "left":
                    self.bullet.rotation += 2.5

            else:
                if self.player.doY == 0:
                    # jump!
                    self.player.doY += self.player.JUMP_SPEED
                    self.player.doGravity = True

        if "S" in keyNames:
            if self.freeze:
                # navigate bullet
                if self.bullet.DIRECTION == "right":
                    self.bullet.rotation += 2.5

                elif self.bullet.DIRECTION == "left":
                    self.bullet.rotation -= 2.5

        if "A" in keyNames:
            # move left
            self.player.doX -= self.player.WALK_SPEED * deltaTime

            self.player.direction = "left"

        if "D" in keyNames:
            # move right
            self.player.doX += self.player.WALK_SPEED * deltaTime

            self.player.direction = "right"

        if "A" not in keyNames and "D" not in keyNames:
            # stop moving left-right

            # MAGIC NUMBER ALERT!!!
            if self.player.doX > -.5 and self.player.doX < .5:
                self.player.doX = 0

            else:
                self.player.doX *= self.player.WALK_SMOOTH

        if "SPACE" in keyNames:
            if not self.freeze:
                # shoot bullet
                if (time.time() - self.player.lastShot) >= self.player.FIRE_RATE:
                    self.bullet = Bullet(self.player.position, self.player.direction, self.player.BULLET_OFFSET)
                    self.bulletMapCollider = BulletMapCollider(self.bullet)

                    self.add(self.bullet)
                    self.bulletStuff.add(self.bullet)

                    self.freeze = True

                    self.player.lastShot = time.time()

        ######################################################

        if not self.freeze:
            # update the player
            self.player.doY -= self.player.GRAVITY_SPEED * deltaTime

            checkMap(self.player, self.playerMapCollider, self.sceneManager.currentLevel.mapLayer)

            # update the enemy `Badputer` instances
            self.badputer.update(deltaTime)

            # make the "camera" follow the player
            self.sceneManager.currentLevel.scroller.set_focus(self.player.position[0], self.player.position[1])

        else:
            if self.bullet.killMe:
                bulletPosition = self.bullet.position
                self.remove(self.bullet)
                for sprite in self.get_children():
                    if isinstance(sprite, BulletTrail):
                        self.remove(sprite)

                explosion = Explosion(bulletPosition)
                self.add(explosion)
                self.tempAnimations.add(explosion)

                self.bullet = None
                self.bulletStuff = set()
                self.bulletMapCollider = None

                self.freeze = False

            else:
                # `48` is the BulletTrail sprite width
                #                    MAGIC NUMBER ALERT!!!                            \/
                if abs(self.bullet.distanceTraveled - self.bullet.lastBulletTrail) >= 48:
                    # check for Bullet collisions with self
                    self.collisionManager.clear()
                    for sprite in self.bulletStuff.union(set([self.player]).union(self.enemies)):
                        self.collisionManager.add(sprite)

                    # handle collisions
                    collisions = self.collisionManager.objs_colliding(self.bullet)
                    if collisions:
                        self.bullet.killMe = True
                        for sprite in self.bulletStuff:
                            if sprite in collisions:
                                self.player.doDamage((float(random.randint(25, 75)) / 100))

                        for sprite in self.enemies:
                            if sprite in collisions:
                                sprite.doDamage((float(random.randint(25, 75)) / 100))

                    bulletTrail = BulletTrail(self.bullet.position, self.bullet.rotation)
                    self.add(bulletTrail)
                    self.bulletStuff.add(bulletTrail)
                    self.bullet.lastBulletTrail = self.bullet.distanceTraveled

                checkMap(self.bullet, self.bulletMapCollider, self.bulletMap, deltaTime = deltaTime)

                # make the "camera" follow the player's bullet
                self.sceneManager.currentLevel.scroller.set_focus(self.bullet.position[0], self.bullet.position[1])

        # look through enemies and remove them if they are dead
        enemiesTemp = self.enemies.copy()
        for sprite in enemiesTemp:
            if sprite.killMe:
                self.remove(sprite)
                self.enemies.remove(sprite)

        tempAnimationsTemp = self.tempAnimations.copy()
        for sprite in tempAnimationsTemp:
            if (time.time() - sprite.startTime) >= sprite.DURATION:
                self.remove(sprite)
                self.tempAnimations.remove(sprite)

    def on_key_press(self, key, modifiers):
        self.keysPressed.add(key)

    def on_key_release(self, key, modifiers):
        self.keysPressed.discard(key)


class Player(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("rawr.png"))):
        self.imageSeq = pyglet.image.ImageGrid(image, 1, 2)
        super(Player, self).__init__(self.imageSeq[1])
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.doX = 0
        self.doY = 0
        self.health = 10

        self.doGravity = True
        self.GRAVITY_SPEED = 10

        self.JUMP_SPEED = 7

        self.WALK_SPEED = 10
        self.WALK_SMOOTH = .85
        self.direction = "right"
        self.lastDirection = "right"

        self.BULLET_OFFSET = ((self.width // 2) + 4, -16)
        self.FIRE_RATE = .25
        self.lastShot = time.time() - self.FIRE_RATE

        self.thruster = Thruster((0, -32))
        self.add(self.thruster)

    def update(self):
        if self.health <= 0:
            pass
            # go to loserScene in sceneManager

        if self.lastDirection != self.direction:
            if self.direction == "left":
                self.image = self.imageSeq[0]

            elif self.direction == "right":
                self.image = self.imageSeq[1]

            self.lastDirection = self.direction

        self.moveBy((self.doX, self.doY))
        self.cshape.center = self.position

        # display the thruster animation
        if self.doY > 0:
            self.thruster.enable()

        else:
            self.thruster.disable()

    def doDamage(self, damage):
        self.health -= damage * 10
        # do damage animation


class Badputer(OurSprite):
    def __init__(self, position, patrolX, image = pyglet.image.load(data.getPath("badputer.png"))):
        super(Badputer, self).__init__(image)
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.SPEED = 50
        self.PATROL_X = patrolX

        self.direction = "left"
        self.doX = -self.SPEED * config.DELTA_TIME
        self.doY = 0
        self.health = 10
        self.killMe = False

    def update(self, deltaTime):
        if self.health <= 0:
            self.killMe = True

        # change direction
        if self.direction == "left" and self.position[0] < self.PATROL_X[0]:
            self.direction = "right"
            self.doX = self.SPEED * deltaTime

        elif self.direction == "right" and self.position[0] > self.PATROL_X[1]:
            self.direction = "left"
            self.doX = -self.SPEED * deltaTime

        self.moveBy((self.doX, self.doY))
        self.cshape.center = self.position

    def doDamage(self, damage):
        self.health -= damage * 10
        # do damage animation


class Bullet(OurSprite):
    def __init__(self, position, direction, offset, image = pyglet.image.load(data.getPath("bam.png"))):
        super(Bullet, self).__init__(image)
        self.position = position
        self.DIRECTION = direction
        self.OFFSET = offset

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.spawnTime = time.time()
        self.killMe = False

        self.doX = 0
        self.doY = 0
        self.rotation = 0
        self.distanceTraveled = 0
        self.lastBulletTrail = 0

        if self.DIRECTION == "left":
            self.SPEED = -200

        elif self.DIRECTION == "right":
            self.SPEED = 200

        else:
            self.SPEED = 0
            print("DIRECTION is messed up!!!")

        self.LIFETIME = 3

    def update(self, deltaTime):
        if (time.time() - self.spawnTime) >= self.LIFETIME:
            self.killMe = True

        else:
            self.distanceTraveled += self.SPEED * deltaTime
            self.doX, self.doY = self.moveForward(self.SPEED * deltaTime, doReturn = True)
            self.cshape.center = self.position


class EnemyBullet(Bullet):
    pass


class BulletTrail(OurSprite):
    def __init__(self, position, rotation, image = pyglet.image.load(data.getPath("bullet_trail.png"))):
        super(BulletTrail, self).__init__(image)
        self.position = position
        self.rotation = rotation

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)


class Explosion(OurSprite):
    def __init__(self, position, image = pyglet.image.load_animation(data.getPath("explosion.gif"))):
        super(Explosion, self).__init__(image)
        self.position = position

        self.startTime = time.time()
        self.DURATION = 1


class Thruster(OurSprite):
    def __init__(self, offset, image = pyglet.image.load_animation(data.getPath("flames.gif"))):
        super(Thruster, self).__init__(image)
        self._image = image

        self.moveBy(offset)

    def disable(self):
        self.opacity = 0

    def enable(self):
        self.opacity = 255


class SpriteMapCollider(cocos.tiles.RectMapCollider):
    def __init__(self, sprite):
        self.sprite = sprite


class PlayerMapCollider(SpriteMapCollider):
    def collide_bottom(self, doY):
        if self.sprite.doY:
            self.sprite.doY = doY
            self.sprite.update()
            self.sprite.doY = 0

    def collide_left(self, doX):
        self.sprite.doX = doX
        self.sprite.update()
        self.sprite.doX = 0

    def collide_right(self, doX):
        self.sprite.doX = doX
        self.sprite.update()
        self.sprite.doX = 0

    def collide_top(self, doY):
        if self.sprite.doY:
            self.sprite.doY = doY
            self.sprite.update()
            self.sprite.doY = 0


class BulletMapCollider(SpriteMapCollider):
    def collide_bottom(self, doY):
        self.sprite.killMe = True

    def collide_left(self, doX):
        self.sprite.killMe = True

    def collide_right(self, doX):
        self.sprite.killMe = True

    def collide_top(self, doY):
        self.sprite.killMe = True


class MainMenu(cocos.menu.Menu):
    def __init__(self, sceneManager):
        super(MainMenu, self).__init__()
        self.sceneManager = sceneManager

        l = []
        l.append(cocos.menu.MenuItem("Start Game", self.onStartGame))
        l.append(cocos.menu.MenuItem("Options", self.onOptions))
        l.append(cocos.menu.MenuItem("Quit Game", self.onQuitGame))
        self.create_menu(l, cocos.menu.shake(), cocos.menu.shake_back())

    def onStartGame(self):
        self.sceneManager.doLevelScene(increment = False)

    def onOptions(self):
        pass

    def onQuitGame(self):
        # GOODBYE!!!  :)
        sys.exit()


def main():

    director.init(width = config.SCREEN_WIDTH, height = config.SCREEN_HEIGHT, resizable = False, caption = "Platformy.py")

    # ONLY FOR DEV
    director.show_FPS = True

    sceneManager = scenes.SceneManager(director)
    levels = [
        scenes.Level(cocos.tiles.load(data.getPath("map.tmx"))["Tile Layer 1"], MainGameLayer(sceneManager))
    ]
    sceneManager.loadScenes(cocos.scene.Scene(MainMenu(sceneManager)), None, None, levels)
    sceneManager.run()
