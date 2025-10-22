class BattleLogger:
    def __init__(self):
        self.logs = []

    def log(self, msg: str):
        # record and print uniformly
        self.logs.append(msg)
        print(msg)

    def export(self):
        return self.logs[:]
