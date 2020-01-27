from .errors import ColorNotSet, BadCard

class Card:
    def __repr__(self):
        return f"{self.__class__.__name__}: {str(self)}"
        # return "%s: %s %s" % (self.__class__.__name__, self.__str__(), str(id(self)))

    def compare(self, card):
        if not isinstance(card, (ColorCard, SpecialCard)):
            raise TypeError

    def __hash__(self):
        return hash(str(self))

class ColorCard(Card):
    # color
    # number
    # compare > color == card.color || number == card.number
    def __init__(self, color, number):
        super().__init__()
        self.color = color
        self.number = int(number)

    def compare(self, card):
        super().compare(card)
        matched_colors = self.color == card.color
        if isinstance(card, ColorCard):
            if not (matched_colors or self.number == card.number): raise BadCard
        elif not matched_colors: raise BadCard

    def __str__(self):
        return f"{self.color} {self.number}"

    def __eq__(self, other):
        if not isinstance(other, ColorCard): return False
        return self.color == other.color and self.number == other.number

    def __hash__(self):
        return super().__hash__()

class SpecialCard(Card):
    # color
    # special
    # compare > color == card.color
    def __init__(self, color, special):
        super().__init__()
        self.color = color
        self.special = special

    def compare(self, card):
        super().compare(card)
        matched_colors = self.color == card.color
        if isinstance(card, SpecialCard):
            if not (matched_colors or self.special == card.special): raise BadCard
        elif not matched_colors: raise BadCard

    def __str__(self):
        return f"{self.color} {self.special}"

    def __eq__(self, other):
        if not isinstance(other, SpecialCard): return False
        return self.color == other.color and self.special == other.special

    def __hash__(self):
        return super().__hash__()

class WildCard(Card):
    # special
    # next_color
    # compare > return True
    def __init__(self, special):
        super().__init__()
        self.special = special
        self.next_color = None

    def set_color(self, color):
        self.next_color = color

    def compare(self, card):
        super().compare(card)
        if not self.next_color: raise ColorNotSet
        elif not self.next_color == card.color: raise BadCard

    def __str__(self):
        return f"special {self.special}"

    def __repr__(self):
        next_color = self.next_color if self.next_color is not None else "NOT SET"
        return f"WildCard: {self.special}, next_color = {next_color}"

    def __eq__(self, other):
        if not isinstance(other, WildCard): return False
        return self.special == other.special

    def __hash__(self):
        return super().__hash__()

CARDS = []

COLORS = ["red", "green", "blue", "yellow"]
NUMBERS = range(0, 10)
SPECIALS = ["+2", "reverse", "skip"]
WILDCARD = ["+4", "change color"]

for color in COLORS:
    for number in NUMBERS:
        CARDS.append(ColorCard(color, number))
    for special in SPECIALS:
        CARDS.append(SpecialCard(color, special))
    for wildcard in WILDCARD:
        CARDS.append(WildCard(wildcard))

# c = ColorCard("RED", 5)
# b = ColorSpecialCard("GREEN", "PLUS_FOUR")
# d = ColorSpecialCard("RED", "PLUS_FOUR")
# print(b.compare(d))