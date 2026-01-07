from enum import Enum, unique


@unique
class SelectionState(Enum):
    SelectionOFF = -1
    SelectPlayer = 0
    SelectCards = 1
    SelectDealer = 2
    SelectPot = 3
    SelectContext = 4

    def color(self, *args, **kwargs):
        if self.value == 0:
            return 'lime'
        elif self.value == 1:
            return 'cyan'
        elif self.value == 2:
            return 'blueviolet'
        elif self.value == 3:
            return 'orange'
        elif self.value == 4:
            return 'red'
        else:
            return 'white'
