from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..card import Card
    
from .scoring import score_hand

__all__ = ["estimate_holding_strength"]


def estimate_holding_strength(
    holding: list["Card"], n_simulations: int = 1000, n_players: int = 8
) -> float:
    """
    Estimate the holding strength as the probability of winning against n_players - 1 opponents.

    Parameters
    ----------
    holding : list[Card]
        The player's holding cards.
    n_simulations : int, optional
        The number of Monte Carlo simulations to run (default is 1000).
    n_players : int, optional
        The total number of players at the table including the player (default is 8).
    """
    from maverick import Deck
    
    n_opponents = n_players - 1
    n_holding_cards = len(holding)
    n_community_cards = 5 - n_holding_cards
    wins = 0

    # run simulations
    for _ in range(n_simulations):
        # start a new deck for each simulation
        deck = Deck.standard_deck(shuffle=True)

        # deal community cards and opponent holdings
        if n_community_cards > 0:
            community_cards = deck.deal(n_community_cards)
        else:
            community_cards = []
        opponent_holdings = [deck.deal(n_holding_cards) for _ in range(n_opponents)]

        # compare scores
        score = score_hand(holding + community_cards)[-1]
        if all(score > score_hand(h + community_cards)[-1] for h in opponent_holdings):
            wins += 1

    return wins / n_simulations
