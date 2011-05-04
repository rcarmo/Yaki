from snakeserver.user import LoginUser

class FileUser(LoginUser):
    def getdirectory(self):
        return self.__directory
    directory=property(getdirectory, None, None, "root directory")

    def __init__(self, userid, name, directory, passwordhash):
        LoginUser.__init__(self, userid, None, name, passwordhash=passwordhash.decode("hex"), privileges=["filemgr_access"])
        self.__directory = directory
