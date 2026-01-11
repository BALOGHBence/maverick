from typing import TYPE_CHECKING, Tuple, Optional
from itertools import combinations
from functools import partial

if TYPE_CHECKING:
    from ..card import Card

from .scoring import find_highest_scoring_hand

__all__ = ["estimate_holding_strength", "estimate_strongest_hand"]


def estimate_holding_strength(
    holding: list["Card"],
    *,
    community_cards: Optional[list["Card"]] = None,
    n_simulations: int = 1000,
    n_players: int = 8,
    n_min_private: int = 0,
    n_community_cards_total: int = 5,
) -> float:
    """
    Estimate the holding strength as the relative linelihood of winning against
    n_players - 1 opponents.

    If you are pre-flop, provide only your two hole cards in `holding`.
    If you are post-flop, provide your two hole cards plus the community cards on the
    table in `community_cards`.

    Parameters
    ----------
    holding : list[Card]
        The player's holding cards.
    n_simulations : int, optional
        The number of Monte Carlo simulations to run (default is 1000).
    n_players : int, optional
        The total number of players at the table including the player (default is 8).
    community_cards : list[Card], optional
        The community cards already on the table. If provided, these will be used in the
        simulations.
    n_community_cards_total : int, optional
        The total number of community cards in the game (default is 5).
    n_min_private : int, optional
        The minimum number of private cards that must be included in the hand (default is 0).

    Returns
    -------
    float
        The relative linelihood of winning as a value in the unit interval [0, 1].

    Notes
    -----
    The estimated strength is only as accurate as the number of simulations run. Also, it is
    only the relative linelihood of winning mathematically, and does not take into account
    betting strategies, player tendencies, or other psychological factors.
    """
    from maverick import Deck

    community_cards = community_cards or []

    n_opponents = n_players - 1
    n_holding_cards = len(holding)
    n_community_cards = len(community_cards)
    n_community_cards_req = n_community_cards_total - n_community_cards
    n_wins = 0

    scorer = partial(find_highest_scoring_hand, n_min_private=n_min_private)

    # run simulations
    for _ in range(n_simulations):
        # start a new deck for each simulation
        deck_sim = Deck.standard_deck().shuffle()

        # remove known cards
        deck_sim.remove_cards(holding + community_cards)

        # deal opponent holdings
        opponent_holdings = [deck_sim.deal(n_holding_cards) for _ in range(n_opponents)]

        # deal community cards and opponent holdings
        community_cards_full = community_cards + deck_sim.deal(n_community_cards_req)

        # compare scores
        score = scorer(holding, community_cards_full)[-1]
        if all(score > scorer(h, community_cards_full)[-1] for h in opponent_holdings):
            n_wins += 1

    return n_wins / n_simulations


def estimate_strongest_hand(
    private_cards: list["Card"],
    community_cards: list["Card"],
    *,
    n_min_private: int = 0,
    n_simulations: int = 1000,
    n_players: int = 8,
    n_community_cards_total: int = 5,
) -> Tuple[list["Card"], float]:
    """
    Estimate the strongest hand from the given private and community cards
    with at least `n_min_private` cards from the private cards.

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
    n_community_cards_total : int, optional
        The total number of community cards in the game (default is 5).

    Returns
    -------
    Tuple[list[Card], float]
        The strongest hand and its estimated strength (relative likelihood of winning).
    """
    all_cards = private_cards + community_cards

    # If we have 5 or fewer cards total, return all of them
    if len(all_cards) <= 5:
        strength = estimate_holding_strength(
            private_cards,
            n_simulations=n_simulations,
            n_players=n_players,
            community_cards=community_cards,
            n_community_cards_total=n_community_cards_total,
        )
        return all_cards, strength

    best_hand = []
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
