from typing import TYPE_CHECKING, Tuple
from itertools import combinations

if TYPE_CHECKING:
    from ..card import Card

from .scoring import score_hand

__all__ = ["estimate_holding_strength", "estimate_strongest_hand"]


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


def estimate_strongest_hand(
    private_cards: list["Card"],
    community_cards: list["Card"],
    n_min_private: int = 0,
    n_simulations: int = 1000,
    n_players: int = 8,
) -> Tuple[list["Card"], float]:
    """
    Estimate the strongest 5-card hand from the given private and community cards
    with at least n_min_private cards from the private cards.

    This uses Monte Carlo simulation to estimate which hand is most likely to win.

    Parameters
    ----------
    private_cards : list[Card]
        The player's private cards.
    community_cards : list[Card]
        The community cards on the table.
    n_min_private : int, optional
        The minimum number of private cards that must be included in the hand (default is 0).
    n_simulations : int, optional
        The number of Monte Carlo simulations to run for strength estimation (default is 1000).
    n_players : int, optional
        The total number of players at the table including the player (default is 8).

    Returns
    -------
    Tuple[list[Card], float]
        The strongest hand and its estimated strength (probability of winning).
    """
    all_cards = private_cards + community_cards

    # If we have 5 or fewer cards total, return all of them
    if len(all_cards) <= 5:
        return all_cards

    best_hand = None
    best_strength = -1.0

    # Generate all possible 5-card combinations
    for hand in combinations(all_cards, 5):
        # Count how many private cards are in this hand
        n_private_in_hand = sum(1 for card in hand if card in private_cards)

        # Skip if doesn't meet minimum private cards requirement
        if n_private_in_hand < n_min_private:
            continue

        # Estimate strength of this hand
        strength = estimate_holding_strength(
            list(hand), n_simulations=n_simulations, n_players=n_players
        )

        # Update best hand if this one is stronger
        if strength > best_strength:
            best_strength = strength
            best_hand = list(hand)

    return best_hand, best_strength
