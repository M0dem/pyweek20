
import cocos

class Level(cocos.scene.Scene):
    def __init__(self, mapLayer, mainGameLayer):
        self.mapLayer = mapLayer
        self.mainGameLayer = mainGameLayer

        self.scroller = cocos.layer.ScrollingManager()
        self.scroller.add(self.mapLayer)
        self.scroller.add(self.mainGameLayer)


class SceneManager():
    def __init__(self, director):
        self.director = director

    def run(self):
        if not self.director.scene:
            self.doMainMenu(run = True)

    def loadScenes(self, mainMenu, loserScene, winnerScene, levels):
        self.mainMenu = mainMenu
        self.loserScene = loserScene
        self.winnerScene = winnerScene
        self.levels = levels
        
        self.currentLevelIndex = 0
        self.updateCurrentLevelStuff()

    def updateCurrentLevelStuff(self):
        self.currentLevel = self.levels[self.currentLevelIndex]
        self.currentLevelScene = cocos.scene.Scene(self.currentLevel.scroller)

    def doMainMenu(self, run = False):
        self.currentLevel = 0
        if run:
            self.director.run(self.mainMenu)

        else:
            self.director.replace(cocos.scene.FlipX3DTransition(self.mainMenu, duration = 1))

    def doLoserScene(self):
        self.currentLevel = 0
        self.director.replace(cocos.scene.FlipX3DTransition(self.loserScene, duration = 1))

    def doWinnerScene(self):
        self.currentLevel = 0
        self.director.replace(cocos.scene.FlipX3DTransition(self.winnerScene, duration = 1))

    def nextLevel(self):
        if (self.currentLevelIndex + 2) < len(self.levels):
            self.currentLevelIndex += 1
            self.updateCurrentLevelStuff()
            self.director.replace(cocos.scene.FlipX3DTransition(self.currentLevelScene, duration = 1))

        else:
            # has completed all the levels
            self.doWinnerScene()
