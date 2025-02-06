import random
from collections import deque
import warnings

from collections import deque
import random
from multiprocessing import Pool, cpu_count

from numpy import mean


class GameHelper:

    def adjust_ace(self, cards):
        """Converts one Ace (11) to 1 if the hand is over 21."""
        found = False  # Track if we've changed one Ace
        return [1 if x == 11 and not found and (found := True) else x for x in cards]

    def handvalue(self, hand_cards):
        """Calculates the total hand value and checks if it's hard/soft."""
        total = sum(hand_cards)
        while total > 21 and 11 in hand_cards:
            hand_cards = self.adjust_ace(hand_cards)
            total = sum(hand_cards)

        is_hard = 11 not in hand_cards
        is_pair = len(hand_cards) == 2 and hand_cards[0] == hand_cards[1]
        return total, is_hard, is_pair  # Returns (total, is_hard)

    def hit(self, hand_cards, shoe):
        """Draws a card from the shoe."""
        # print(f"hit{shoe}")
        if len(shoe) == 0:
            raise Exception("The shoe is empty!")
        new_card = shoe.popleft()
        hand_cards.append(new_card)
        # print(f"Receives {'a' if new_card != 11 else 'an'} {new_card if new_card != 11 else 'ace'}.")
        return new_card

    def dealer_play(self, hand):
        """Handles dealer's turn, following the standard rules."""
        total, hard, _ = self.handvalue(hand)
        # print(f'Dealer is in play and has {total}.')

        while total < 17 or (total == 17 and not hard):  # Dealer hits on soft 17
            self.hit(hand, self.shoe)
            total, hard, _ = self.handvalue(hand)
            # print(f'Dealer is now at {total}')

        # if total > 21:
            # print("Dealer busts.")
        return total


class Player(GameHelper):
    def __init__(self, bankroll, shoe):
        super().__init__()
        self.bankroll = bankroll
        self.shoe = shoe
        self.hands = []

    def player_game_complete(self):
        for hand in self.hands:
            if hand[0] == False:
                return False
        return True

    def player_strategy(self, hand_cards, dealer_upcard):
        total, is_hard, is_pair = self.handvalue(hand_cards)
        if is_pair and len(hand_cards) == 2:
            pair = (hand_cards[0], hand_cards[1])
        elif (total == 12 and is_hard == False):
            pair = (1, 1)
        else:
            pair = None

        hard_totals = {
            17: 'stand', 18: 'stand', 19: 'stand', 20: 'stand', 21: 'stand',
            16: 'stand' if dealer_upcard in [2, 3, 4, 5, 6] else 'hit',
            15: 'stand' if dealer_upcard in [2, 3, 4, 5, 6] else 'hit',
            14: 'stand' if dealer_upcard in [2, 3, 4, 5, 6] else 'hit',
            13: 'stand' if dealer_upcard in [2, 3, 4, 5, 6] else 'hit',
            12: 'stand' if dealer_upcard in [4, 5, 6] else 'hit',
            11: 'double',
            10: 'double' if dealer_upcard <= 9 else 'hit',
            9: 'double' if dealer_upcard in [3, 4, 5, 6] else 'hit'
        }

        soft_totals = {
            20: 'stand', 21: 'stand',
            19: 'double' if dealer_upcard == 6 else 'stand',
            18: 'double' if dealer_upcard in [3, 4, 5, 6] else 'stand' if dealer_upcard in [2, 7, 8] else 'hit',
            17: 'double' if dealer_upcard in [3, 4, 5, 6] else 'hit',
            16: 'double' if dealer_upcard in [4, 5, 6] else 'hit',
            15: 'double' if dealer_upcard in [4, 5, 6] else 'hit',
            14: 'double' if dealer_upcard in [5, 6] else 'hit',
            13: 'double' if dealer_upcard in [5, 6] else 'hit',
        }

        pair_splits = {
            (8, 8): 'split', (1, 1): 'split',
            (2, 2): 'split' if dealer_upcard in [2, 3, 4, 5, 6, 7] else 'hit',
            (3, 3): 'split' if dealer_upcard in [2, 3, 4, 5, 6, 7] else 'hit',
            (4, 4): 'split' if dealer_upcard in [5, 6] else 'hit',
            (5, 5): 'double' if dealer_upcard in [2, 3, 4, 5, 6, 7] else 'hit',
            (6, 6): 'split' if dealer_upcard in [2, 3, 4, 5, 6] else 'hit',
            (7, 7): 'split' if dealer_upcard in [2, 3, 4, 5, 6, 7] else 'hit',
            (9, 9): 'split' if dealer_upcard not in [7, 10, 11] else 'stand'
        }

        # Check for pair split scenario
        if pair in pair_splits:
            return pair_splits[pair]

        # Check for soft totals (hand contains an Ace counted as 11)
        if not is_hard and total <= 21:
            return soft_totals.get(total, 'hit')

        # Default to hard total strategy
        return hard_totals.get(total, 'hit')

    def double(self, hand):
        self.bankroll -= hand[1]
        hand[0] = True
        hand[1] *= 2
        self.hit(hand[2], self.shoe)

    def split(self, hand):
        if hand[2][0] != hand[2][1]:
            warnings.warn("The hand being split is not a pair!")

        self.bankroll -= hand[1]
        index = self.hands.index(hand)
        split_hands1 = [False, hand[1], [hand[2][0]]]
        split_hands2 = [False, hand[1], [hand[2][0]]]


        del self.hands[index]
        self.hands.insert(index, split_hands1)
        self.hands.insert(index + 1, split_hands2)

    def player_action(self, hand, dealer_upcard):
        # print(hand)
        action = self.player_strategy(hand[2], dealer_upcard)

        if action == 'stand':
            # print(action)
            hand[0] = True

        elif action == 'hit':
            # print(action)
            self.hit(hand[2], self.shoe)
            # print(hand[2])
            if self.handvalue(hand[2])[0] > 21:
                hand[0] = True

        elif action == 'double':
            # print(action)
            self.double(hand)

        elif action == 'split':
            # print(action)
            self.split(hand)



class Game(GameHelper):
    def __init__(self):
        super().__init__()
        self.shoe = self.shuffle_shoe()
        self.dealer_hand = []
        self.player = Player(100000, self.shoe)
        self.count = [0]


    def shuffle_shoe(self):
        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        shoe = deque(deck * 6)  # 6-deck shoe
        random.shuffle(shoe)
        # shoe = deque([9, 4, 2, 2 , 7, 7, 10 ,10, 10, 10, 10, 10, 10, 10, 10])
        return shoe
    def check_shoe(self):
        if len(self.shoe) < 52 * 1.5:
            new_shoe = self.shuffle_shoe()
            self.shoe = new_shoe
            self.player.shoe = new_shoe

    def deal_cards(self, player_bets):
        for bet in range(len(player_bets)):
            self.player.hands.append([False, player_bets[bet], []])
            self.player.bankroll -= player_bets[bet]
        for _ in range(2):
            for hand in self.player.hands:
                self.hit(hand[2], self.shoe)
            self.hit(self.dealer_hand, self.shoe)

    def player_play_complete(self):
        for hand in self.player.hands:
            if hand[0] == False:
                return False
        return True

    def remove_loss(self, dealer_total):
        for i in range(len(self.player.hands) - 1, -1, -1):
            hand_value = self.handvalue(self.player.hands[i][2])[0]
            if hand_value > 21 or (hand_value < dealer_total <= 21):
                # print(f"Player loses hand: {self.player.hands[i]}")
                del self.player.hands[i]

    def return_push(self, dealer_total):
        for i in range(len(self.player.hands) - 1, -1, -1):
            hand_value = self.handvalue(self.player.hands[i][2])[0]
            if 21 >= hand_value == dealer_total:
                # print(f"Player pushes hand: {self.player.hands[i]}")
                self.player.bankroll += self.player.hands[i][1]
                del self.player.hands[i]

    def pay_wins(self, dealer_total):
        for i in range(len(self.player.hands) - 1, -1, -1):
            hand_value = self.handvalue(self.player.hands[i][2])[0]
            if 21 >= hand_value:
                # print(f"Player wins hand: {self.player.hands[i]}")
                self.player.bankroll += self.player.hands[i][1] * 2
                del self.player.hands[i]

    def pay_blackjacks(self):
        for i in range(len(self.player.hands) - 1, -1, -1):
            hand_value = self.handvalue(self.player.hands[i][2])[0]
            if hand_value == 21:
                self.player.bankroll += self.player.hands[i][1] * 2.5
                del self.player.hands[i]

    def endgame(self, dealer_total):
        self.remove_loss(dealer_total)
        self.return_push(dealer_total)
        self.pay_wins(dealer_total)

    def play(self):
        self.check_shoe()

        self.deal_cards([1])

        dealer_total = self.handvalue(self.dealer_hand)[0]
        if dealer_total == 21:
            self.endgame(dealer_total)
            return
        for hand in self.player.hands:
            if self.handvalue(hand[2])[0] == 21:
                self.pay_blackjacks()
                break

        i = 0
        while i < len(self.player.hands):
            # Use index-based iteration
            hand = self.player.hands[i]  # Get the current hand
            while not hand[0]:  # Process the hand
                # print(self.player.hands)
                self.player.player_action(hand, self.dealer_hand[0])
                hand = self.player.hands[i]
                # print(self.player.hands)
            i += 1  # Move to the next hand

        self.dealer_play(self.dealer_hand)
        dealer_total = self.handvalue(self.dealer_hand)[0]
        self.endgame(dealer_total)
        if len(self.player.hands) != 0:
            # print(self.player.hands)
            raise Exception("Not all hands processed.")
        self.dealer_hand = []


def run_game(_):
    """Runs one game and returns the final bankroll."""
    game = Game()
    for i in range(100000):
        game.play()
    return game.player.bankroll

if __name__ == '__main__':
    pool = Pool()
    bankroll = pool.map(run_game, range(20))
    pool.close()
    pool.join()
    print('donezo')
    print(bankroll)
    print(mean(bankroll))

