#!/usr/bin/env python3
"""Altitude data + helpers (shared by model, tuner, fixture builder).

Effect model (documented, backtestable): a team is disadvantaged by playing
ABOVE its home altitude. disadvantage = max(0, venue_alt - home_alt). The goal
supremacy gains ALT_COEF * (disadvantage_opponent - disadvantage_self).
At a sea-level venue both disadvantages are ~0 -> no effect.
"""
DEFAULT_ALT = 50

# Home altitude (m) of the main national venue. Only elevated nations listed;
# everyone else defaults to ~sea level. Keyed by results.csv team names.
ALT = {
    'Bolivia': 3640, 'Ecuador': 2850, 'Colombia': 2640, 'Yemen': 2250,
    'Eritrea': 2325, 'Ethiopia': 2355, 'Bhutan': 2320, 'Mexico': 2240,
    'Afghanistan': 1790, 'Lesotho': 1600, 'Kenya': 1660, 'South Africa': 1600,
    'Rwanda': 1560, 'Guatemala': 1500, 'Zimbabwe': 1490, 'Nepal': 1400,
    'Mongolia': 1300, 'Zambia': 1280, 'Madagascar': 1280, 'Uganda': 1200,
    'Iran': 1190, 'Costa Rica': 1170, 'Eswatini': 1100, 'Honduras': 1000,
    'Armenia': 990, 'Kyrgyzstan': 800, 'Tajikistan': 800, 'Cameroon': 720,
    'Saudi Arabia': 600, 'Spain': 600, 'Burundi': 1700, 'Malawi': 1050,
}

# teams.csv name -> results.csv name (only the differing ones)
NAME2RESULTS = {'Bosnia': 'Bosnia and Herzegovina', 'Curacao': 'Curaçao',
                'Czechia': 'Czech Republic', 'Turkiye': 'Turkey',
                'USA': 'United States', 'Congo DR': 'DR Congo'}

# 2026 host venues (results.csv city strings) -> altitude (m)
VENUE_ALT = {
    'Mexico City': 2240, 'Zapopan': 1560, 'Guadalupe': 540, 'Atlanta': 320,
    'Kansas City': 270, 'Arlington': 180, 'Toronto': 76, 'Seattle': 55,
    'Inglewood': 40, 'Foxborough': 30, 'Houston': 30, 'Philadelphia': 12,
    'Santa Clara': 8, 'East Rutherford': 5, 'Vancouver': 4, 'Miami Gardens': 3,
}

def home_alt(team):
    return ALT.get(NAME2RESULTS.get(team, team), DEFAULT_ALT)

def alt_supremacy(venue_alt, alt_home, alt_away, coef):
    """Goal-supremacy bonus to the home/first team from altitude acclimatisation."""
    dis_home = max(0, venue_alt - alt_home)
    dis_away = max(0, venue_alt - alt_away)
    return coef * (dis_away - dis_home)
