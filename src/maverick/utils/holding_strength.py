from typing import TYPE_CHECKING, Optional
from functools import partial

if TYPE_CHECKING:  # pragma: no cover
    from ..card import Card

from .scoring import find_highest_scoring_hand

__all__ = ["estimate_holding_strength"]


def estimate_holding_strength(
    holding: list["Card"],
    *,
    community_cards: Optional[list["Card"]] = None,
    n_simulations: int = 1000,
    n_players: int = 8,
    n_private: int = 0,
    n_community_cards_total: int = 5,
) -> float:
    """
    Estimate the holding strength as the relative linelihood of winning against
    n_players - 1 opponents.

    If you are pre-flop, provide only your two hole cards in `holding`.
    If you are post-flop, provide your hole cards plus the community cards on the
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
    n_private : int, optional
        The number of private cards that must be included in the hand (default is 0).

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

    scorer = partial(find_highest_scoring_hand, n_private=n_private)

    # run simulations
    for _ in range(n_simulations):
        # start a new deck for each simulation
        deck_sim = Deck.standard_deck().shuffle()

        # remove known cards
        deck_sim.remove_cards(holding + community_cards)

        # deal opponent holdings
        opponent_holdings = [deck_sim.deal(n_holding_cards) for _ in range(n_opponents)]

        # deal missing community cards
        if n_community_cards_req > 0:
            community_cards_full = community_cards + deck_sim.deal(
                n_community_cards_req
            )
        else:
            community_cards_full = community_cards

        # compare scores
        score = scorer(holding, community_cards_full)[-1]
        if all(score >= scorer(h, community_cards_full)[-1] for h in opponent_holdings):
            n_wins += 1

    return n_wins / n_simulations
