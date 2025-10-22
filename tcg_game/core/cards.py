class Card:
    def __init__(self, name, ctype, power=0, description=""):
        self.name = name
        self.type = ctype   # attack / defense / heal / special
        self.power = power
        self.description = description

    def use(self, user, target):
        """Efek default (akan di-override oleh kartu spesifik)."""
        print(f"{user.name} uses {self.name} on {target.name}.")
