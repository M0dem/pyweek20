# entry point from `run_game.py`

from cocos import collision_model
from cocos.director import director

import cocos
import copy
import math
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


def angleFromPoints(positionA, positionB):
    deltaY = positionB[1] - positionA[1]
    deltaX = positionB[0] - positionA[0]
    return math.atan2(deltaY, deltaX) * 180 / math.pi


def getLevels(sceneManager):
    levels = [
        scenes.Level(
            cocos.tiles.load(data.getPath("map.tmx"))["Tile Layer 1"],
            MainGameLayer(sceneManager),
            cocos.text.Label(text = "", position = (config.SCREEN_WIDTH // 12, config.SCREEN_HEIGHT // 12)),
            playerSpawn = (300, 600),
            winBlockSpawn = (1536 - 32, 1024 - 32),
            badputerSpawns = ((125, 875), (500, 500), (1000, 700), (1200, 450), (0, 0)),
            levelDifficulty = .75
        ),
        scenes.Level(
            cocos.tiles.load(data.getPath("map.tmx"))["Tile Layer 1"],
            MainGameLayer(sceneManager),
            cocos.text.Label(text = "", position = (config.SCREEN_WIDTH // 12, config.SCREEN_HEIGHT // 12)),
            playerSpawn = (300, 600),
            winBlockSpawn = (1536 - 32, 1024 - 32),
            badputerSpawns = ((100, 100), (400, 400), (600, 600), (800, 800), (1000, 1000)),
            levelDifficulty = .75
        )
    ]

    return levels


class MainGameLayer(cocos.layer.ScrollableLayer):

    is_event_handler = True

    def __init__(self, sceneManager):
        super(MainGameLayer, self).__init__()
        self.sceneManager = sceneManager

        self.freeze = False

        self.keysPressed = set()

        self.schedule(self.update)

        self.MAP_WIDTH = 1536
        self.MAP_HEIGHT = 1024

        self.background = cocos.sprite.Sprite(pyglet.image.load(data.getPath("background.png")))
        self.background.position = (self.MAP_WIDTH // 2, self.MAP_HEIGHT // 2)
        self.add(self.background)


        self.collisionManager = collision_model.CollisionManagerBruteForce()

        self.bullet = None
        self.bulletStuff = set()
        self.bulletMap = cocos.tiles.load(data.getPath("bullet_map.tmx"))["Tile Layer 1"]
        self.bulletMapCollider = None

        self.tempAnimations = set()

        self.dead = False
        self.isSpaceDown = False
        self.hasSpawned = False

    def update(self, deltaTime):
        if not self.hasSpawned:
            self.doSpawn()

        keyNames = [pyglet.window.key.symbol_string(k) for k in self.keysPressed]

        ######################################################

        if "W" in keyNames or "UP" in keyNames:
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

        if "S" in keyNames or "DOWN" in keyNames:
            if self.freeze:
                # navigate bullet
                if self.bullet.DIRECTION == "right":
                    self.bullet.rotation += 2.5

                elif self.bullet.DIRECTION == "left":
                    self.bullet.rotation -= 2.5

        if "A" in keyNames or "LEFT" in keyNames:
            if not self.freeze:
                # move left
                self.player.doX -= self.player.WALK_SPEED * deltaTime

                self.player.direction = "left"

        if "D" in keyNames or "RIGHT" in keyNames:
            if not self.freeze:
                # move right
                self.player.doX += self.player.WALK_SPEED * deltaTime

                self.player.direction = "right"

        if ("A" not in keyNames and "D" not in keyNames) and ("LEFT" not in keyNames and "RIGHT" not in keyNames):
            if not self.freeze:
                # stop moving left-right

                # MAGIC NUMBER ALERT!!!
                if self.player.doX > -.5 and self.player.doX < .5:
                    self.player.doX = 0

                else:
                    self.player.doX *= self.player.WALK_SMOOTH

        if "SPACE" in keyNames:
            if not self.freeze and not self.isSpaceDown:
                self.isSpaceDown = True
                # shoot bullet
                if (time.time() - self.player.lastShot) >= self.player.FIRE_RATE:
                    self.bullet = Bullet(self.player.position, self.player.direction, self.player.BULLET_OFFSET, levelDifficulty = self.levelDifficulty)
                    self.bulletMapCollider = BulletMapCollider(self.bullet)

                    self.add(self.bullet)
                    # self.bulletStuff.add(self.bullet)

                    self.freeze = True

                    self.player.lastShot = time.time()

        else:
            self.isSpaceDown = False

        ######################################################

        if not self.freeze:
            # update the player
            self.player.doY -= self.player.GRAVITY_SPEED * deltaTime

            checkMap(self.player, self.playerMapCollider, self.sceneManager.currentLevel.mapLayer)



            self.collisionManager.clear()
            for sprite in self.enemies.union(set([self.player])):
                self.collisionManager.add(sprite)

            # update the enemy `Badputer` instances
            for sprite in self.enemies:
                if self.player in self.collisionManager.objs_near(sprite, sprite.RANGE) and (time.time() - sprite.lastShot) > sprite.FIRE_RATE:
                    # shoot!
                    if sprite.x > self.player.x:
                        direction = "left"

                    elif sprite.x < self.player.x:
                        direction = "right"

                    if direction == sprite.direction:
                        enemyBullet = EnemyBullet(sprite.position, sprite.direction, -16, levelDifficulty = self.levelDifficulty)
                        self.add(enemyBullet)
                        sprite.bullets.add(enemyBullet)
                        self.enemyBullets.add(enemyBullet)

                        sprite.lastShot = time.time()

                sprite.update(deltaTime)

            # make the "camera" follow the player
            self.sceneManager.currentLevel.scroller.set_focus(self.player.position[0], self.player.position[1])

            # check for enemy bullet hits on the player
            self.collisionManager.clear()
            for sprite in self.playerBullets.union(set([self.player])):
                self.collisionManager.add(sprite)

            for enemyBullet in self.enemyBullets:
                # check for EnemyBullet collisions with the player and their Bullets

                # handle collisions
                collisions = self.collisionManager.objs_colliding(enemyBullet)
                if collisions:
                    enemyBullet.killMe = True
                    if self.player in collisions:
                        self.player.doDamage(random.randint(15, 25))

        else:
            if self.bullet.killMe:
                if self.bullet.damagePlayer:
                    self.player.doDamage(random.randint(15, 25))

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
                # `32` is the BulletTrail sprite width
                #                    MAGIC NUMBER ALERT!!!                            \/
                if abs(self.bullet.distanceTraveled - self.bullet.lastBulletTrail) >= 48:
                    # check for Bullet collisions with self
                    self.collisionManager.clear()
                    for sprite in self.bulletStuff.union(set([self.player])).union(self.enemies):
                        self.collisionManager.add(sprite)

                    # handle collisions
                    collisions = self.collisionManager.objs_colliding(self.bullet)
                    if collisions:
                        self.bullet.killMe = True
                        for sprite in self.bulletStuff:
                            if sprite in collisions:
                                self.player.doDamage(random.randint(15, 25))

                        for sprite in self.enemies:
                            if sprite in collisions:
                                sprite.doDamage(random.randint(40, 70))

                    bulletTrail = BulletTrail(self.bullet.position, self.bullet.rotation)
                    self.add(bulletTrail)
                    self.bulletStuff.add(bulletTrail)
                    self.playerBullets.add(bulletTrail)
                    self.bullet.lastBulletTrail = self.bullet.distanceTraveled

                self.collisionManager.clear()
                for sprite in self.playerBullets:
                    self.collisionManager.add(sprite)

                for sprite in self.enemyBullets:
                    collisions = self.collisionManager.objs_colliding(sprite)
                    if collisions:
                        sprite.killMe = True
                        for playerBullet in self.playerBullets:
                            if playerBullet in collisions:
                                playerBullet.killMe = True

                checkMap(self.bullet, self.bulletMapCollider, self.bulletMap, deltaTime = deltaTime)

                # if the bullet goes of the map, kill it
                if (self.bullet.position[0] < 0 or self.bullet.position[0] > self.MAP_WIDTH) or (self.bullet.position[1] < 0 or self.bullet.position[1] > self.MAP_HEIGHT):
                    self.bullet.killMe = True
                    self.player.doDamage(random.randint(15, 25))

                # make the "camera" follow the player's bullet
                self.sceneManager.currentLevel.scroller.set_focus(self.bullet.position[0], self.bullet.position[1])

        if self.player.killMe and not self.dead:
            self.playerKilled()
            self.dead = True

        # look through all the enemies and remove them if they are dead
        enemiesTemp = self.enemies.copy()
        for sprite in enemiesTemp:
            if sprite.killMe:
                self.remove(sprite)
                self.enemies.remove(sprite)

                for bullet in sprite.bullets:
                    bullet.killMe = True

        enemyBulletsTemp = self.enemyBullets.copy()
        for sprite in enemyBulletsTemp:
            if sprite.killMe:
                self.remove(sprite)
                self.enemyBullets.remove(sprite)

        tempAnimationsTemp = self.tempAnimations.copy()
        for sprite in tempAnimationsTemp:
            if (time.time() - sprite.startTime) >= sprite.DURATION:
                self.remove(sprite)
                self.tempAnimations.remove(sprite)

        # if the player is lower than like |x: 0|, it is dead!
        if not self.dead:
            if self.player.position[1] < 0:
                self.dead = True
                self.playerKilled()

        # if the player touches the winBlock
        self.collisionManager.clear()
        if not self.dead:
            if self.collisionManager.they_collide(self.player, self.winBlock):
                if (self.numberOfEnemies - len(self.enemies)) >= int(float(2) / 3 * self.numberOfEnemies):
                    self.dead = True
                    self.playerWon()

        # update the player health label
        playerHealthLayer = self.sceneManager.currentLevel.playerHealthLayer
        super(playerHealthLayer.__class__, playerHealthLayer).__init__(text = str(+self.player.health), position = playerHealthLayer.position, font_size = 24, anchor_x = "center", anchor_y = "center", color = (0, 155, 20, 255))

    def doSpawn(self):
        self.hasSpawned = True
        self.level = self.sceneManager.currentLevel
        self.levelDifficulty = self.level.levelDifficulty

        self.player = Player(self.level.playerSpawn)
        self.add(self.player)
        self.playerMapCollider = PlayerMapCollider(self.player)
        self.playerBullets = set()

        self.winBlock = WinBlock(self.level.winBlockSpawn)
        self.add(self.winBlock)

        self.enemies = set()
        self.enemyBullets = set()
        self.numberOfEnemies = len(self.level.badputerSpawns)
        for spawn in self.level.badputerSpawns:
            badputer = Badputer(spawn, self.player, (spawn[0], spawn[0] + 200))
            self.add(badputer)
            self.enemies.add(badputer)


    def playerKilled(self):
        self.sceneManager.doLoserScene()

    def playerWon(self):
        self.sceneManager.doWinnerScene()

    def reset(self):
        self.sceneManager.loadLevels(getLevels(self.sceneManager))

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
        self.health = 100
        self.killMe = False

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
            self.health = 0
            self.killMe = True

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
        self.health -= damage
        # do damage animation


class Badputer(OurSprite):
    def __init__(self, position, target, patrolX, range = 100, image = pyglet.image.load(data.getPath("badputer.png"))):
        super(Badputer, self).__init__(image)
        self.position = position
        self.target = target
        self.PATROL_X = patrolX
        self.RANGE = range

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)

        self.SPEED = 50

        self.direction = "left"
        self.doX = -self.SPEED * config.DELTA_TIME
        self.doY = 0
        self.health = 100
        self.killMe = False
        self.bullets = set()
        self.FIRE_RATE = 1
        self.lastShot = time.time() - self.FIRE_RATE

    def update(self, deltaTime):
        if self.health <= 0:
            self.killMe = True

        for bullet in self.bullets:
            # update the bullets to follow the player
            bullet.rotation = -angleFromPoints(bullet.position, self.target.position)
            bullet.update(deltaTime)

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
        self.health -= damage
        # do damage animation


class Bullet(OurSprite):
    def __init__(self, position, direction, offset, levelDifficulty = 1, image = pyglet.image.load(data.getPath("bam.png"))):
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
        self.damagePlayer = False
        self.DEFAULT_SPEED = 400
        self.LIFETIME = 3

        self.setSpeed(levelDifficulty)

    def update(self, deltaTime):
        '''if (time.time() - self.spawnTime) >= self.LIFETIME:
            self.killMe = True

        else:'''
        self.distanceTraveled += self.SPEED * deltaTime
        self.doX, self.doY = self.moveForward(self.SPEED * deltaTime, doReturn = True)
        self.cshape.center = self.position

    def setSpeed(self, levelDifficulty):
        if self.DIRECTION == "left":
            self.SPEED = -self.DEFAULT_SPEED * levelDifficulty

        elif self.DIRECTION == "right":
            self.SPEED = self.DEFAULT_SPEED * levelDifficulty

        else:
            self.SPEED = 0
            print("DIRECTION is messed up!!!")


class EnemyBullet(Bullet):
    def update(self, deltaTime):
        self.doX, self.doY = self.moveForward(self.SPEED * deltaTime, doReturn = True)
        self.cshape.center = self.position

    def setSpeed(self, levelDifficulty):
        self.image = pyglet.image.load(data.getPath("bawm.png"))
        self.SPEED = self.DEFAULT_SPEED * levelDifficulty


class BulletTrail(OurSprite):
    def __init__(self, position, rotation, image = pyglet.image.load(data.getPath("bam.png"))):
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


class WinBlock(OurSprite):
    def __init__(self, position, image = pyglet.image.load(data.getPath("win_block.png"))):
        super(WinBlock, self).__init__(image)
        self.position = position

        self.cshape = collision_model.AARectShape(self.position, self.width // 2, self.height // 2)


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
        self.sprite.damagePlayer = True

    def collide_left(self, doX):
        self.sprite.killMe = True
        self.sprite.damagePlayer = True

    def collide_right(self, doX):
        self.sprite.killMe = True
        self.sprite.damagePlayer = True

    def collide_top(self, doY):
        self.sprite.killMe = True
        self.sprite.damagePlayer = True


class MainMenu(cocos.menu.Menu):
    def __init__(self, sceneManager, title = ""):
        super(MainMenu, self).__init__(title = title)
        self.sceneManager = sceneManager

        l = []
        l.append(cocos.menu.MenuItem("Start Game", self.onStartGame))
        l.append(cocos.menu.MenuItem("Quit Game", self.onQuitGame))
        self.create_menu(l, cocos.menu.shake(), cocos.menu.shake_back())

    def onStartGame(self):
        self.sceneManager.doLevelScene(increment = False)

    def onQuitGame(self):
        # GOODBYE!!!  :)
        sys.exit()


class TemporaryLabel(cocos.text.Label):
    def __init__(self, sceneManager, loserScene = False, endScene = False, duration = 3, text = "", position = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2), font_size = 32, anchor_x = "center", anchor_y = "center"):
        super(TemporaryLabel, self).__init__(text = text, position = position, font_size = font_size, anchor_x = anchor_x, anchor_y = anchor_y)
        self.sceneManager = sceneManager
        self.loserScene = loserScene
        self.endScene = endScene
        self.duration = duration

        self.age = 0
        self.dead = False

        self.schedule(self.update)

    def update(self, deltaTime):
        if not self.dead:
            self.age += deltaTime
            if self.age >= self.duration:
                self.dead = True
                self.age = 0

                print()
                print(self.endScene)
                print()

                if self.loserScene:
                    self.sceneManager.doLevelScene(increment = False, reset = self)

                elif self.endScene:
                    self.sceneManager.doMainMenuScene()

                else:
                    self.sceneManager.doLevelScene(reset = self)


def main():

    director.init(width = config.SCREEN_WIDTH, height = config.SCREEN_HEIGHT, resizable = False, caption = "Platformy.py")

    # ONLY FOR DEV
    # director.show_FPS = True

    sceneManager = scenes.SceneManager(director)

    loserScene = cocos.scene.Scene(TemporaryLabel(sceneManager, loserScene = True, text = "You lost that level.  :("))
    winnerScene = cocos.scene.Scene(TemporaryLabel(sceneManager, text = "You won that level!  :)"))
    endScene = cocos.scene.Scene(TemporaryLabel(sceneManager, endScene = True, text = "You have won the whole game!  :D"))

    sceneManager.loadScenes(cocos.scene.Scene(MainMenu(sceneManager, title = "Data Snake")), loserScene, winnerScene, endScene, getLevels(sceneManager))
    sceneManager.run()
