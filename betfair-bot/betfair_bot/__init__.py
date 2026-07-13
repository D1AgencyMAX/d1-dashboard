"""Betfair daily research-and-bet bot.

Scans every suitable Betfair market each day, researches each event from
multiple sources, estimates fair probabilities, compares them with executable
exchange prices and places only bets with a statistically validated edge.

The most important rule: the bot is allowed to conclude that there are no
qualifying bets today.
"""

__version__ = "0.1.0"
