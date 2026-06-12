"""
Constantes e mapeamentos para a aplicação de simulação de corridas de F1.
"""

# Todos os anos de 2018 a 2026
ANOS_F1 = [str(ano) for ano in range(2018, 2027)]

# Todos os GPs de 2018 a 2026 
todos_anos = list(range(2018, 2027))

# Mapeamento histórico dos pilotos (2018 a 2026)
PILOTOS_F1 = {
    "ALB": [2019, 2020, 2022, 2023, 2024, 2025, 2026],
    "ALO": [2018, 2021, 2022, 2023, 2024, 2025, 2026],
    "ANT": [2025, 2026], 
    "BEA": [2024, 2025, 2026], 
    "BOR": [2025, 2026], 
    "BOT": todos_anos,
    "COL": [2024], 
    "DEV": [2022, 2023],
    "DOO": [2024, 2025 ], 
    "ERI": [2018], 
    "GAS": todos_anos,
    "GIO": [2019, 2020, 2021],
    "GRO": [2018, 2019, 2020],
    "HAM": todos_anos,
    "HAR": [2018], 
    "HUL": [2018, 2019, 2020, 2022, 2023, 2024, 2025, 2026],
    "KUB": [2019, 2021],
    "KVY": [2019, 2020],
    "LAW": [2023, 2024, 2025, 2026],
    "LEC": todos_anos,
    "MAG": [2018, 2019, 2020, 2022, 2023, 2024],
    "MAZ": [2021],
    "MSC": [2021, 2022],
    "NOR": [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "OCO": [2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "PER": todos_anos,
    "PIA": [2023, 2024, 2025, 2026],
    "RAI": [2018, 2019, 2020, 2021],
    "RIC": [2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "RUS": [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "SAI": todos_anos,
    "SAR": [2023, 2024],
    "SIR": [2018], 
    "STR": todos_anos,
    "TSU": [2021, 2022, 2023, 2024, 2025],
    "VAN": [2018], 
    "VER": todos_anos,
    "VET": [2018, 2019, 2020, 2021, 2022],
    "ZHO": [2022, 2023, 2024]
}

# Calendário com chave "years" adicionada
CIRCUITOS_F1 = {
    "70th Anniversary": {"laps": 52, "chaos": 0.35, "years": [2020]},
    "Abu Dhabi": {"laps": 58, "chaos": 0.40, "years": todos_anos},
    "Australia": {"laps": 58, "chaos": 0.75, "years": [2018, 2019, 2022, 2023, 2024, 2025, 2026]},
    "Austria": {"laps": 71, "chaos": 0.50, "years": todos_anos},
    "Azerbaijan": {"laps": 51, "chaos": 1.00, "years": [2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026]},
    "Bahrain": {"laps": 57, "chaos": 0.40, "years": todos_anos},
    "Barcelona": {"laps": 66, "chaos": 0.50, "years": todos_anos},
    "Belgium": {"laps": 44, "chaos": 0.80, "years": todos_anos},
    "Brazil": {"laps": 71, "chaos": 0.65, "years": [2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026]},
    "Canada": {"laps": 70, "chaos": 0.83, "years": [2018, 2019, 2022, 2023, 2024, 2025, 2026]},
    "China": {"laps": 56, "chaos": 0.50, "years": [2018, 2019, 2024, 2025, 2026]},
    "Eifel": {"laps": 60, "chaos": 0.50, "years": [2020]},
    "Emilia Romagna": {"laps": 63, "chaos": 0.60, "years": [2020, 2021, 2022, 2024, 2025]},
    "France": {"laps": 53, "chaos": 0.30, "years": [2018, 2019, 2021, 2022]},
    "Germany": {"laps": 67, "chaos": 0.60, "years": [2018, 2019]},
    "Great Britain": {"laps": 52, "chaos": 0.65, "years": todos_anos},
    "Hungary": {"laps": 70, "chaos": 0.40, "years": todos_anos},
    "Italy": {"laps": 53, "chaos": 0.55, "years": todos_anos},
    "Japan": {"laps": 53, "chaos": 0.55, "years": [2018, 2019, 2022, 2023, 2024, 2025, 2026]},
    "Las Vegas": {"laps": 50, "chaos": 0.90, "years": [2023, 2024, 2025, 2026]},
    "Madrid": {"laps": 57, "chaos": 0.80, "years": [2026]},
    "Mexico": {"laps": 71, "chaos": 0.50, "years": [2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026]},
    "Miami": {"laps": 57, "chaos": 0.70, "years": [2022, 2023, 2024, 2025, 2026]},
    "Monaco": {"laps": 78, "chaos": 1.00, "years": [2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026]},
    "Netherlands": {"laps": 72, "chaos": 0.70, "years": [2021, 2022, 2023, 2024, 2025, 2026]},
    "Portugal": {"laps": 66, "chaos": 0.40, "years": [2020, 2021]},
    "Qatar": {"laps": 57, "chaos": 0.50, "years": [2021, 2023, 2024, 2025, 2026]},
    "Russia": {"laps": 53, "chaos": 0.45, "years": [2018, 2019, 2020, 2021]},
    "Sakhir": {"laps": 87, "chaos": 0.65, "years": [2020]},
    "Saudi Arabia": {"laps": 50, "chaos": 0.90, "years": [2021, 2022, 2023, 2024, 2025, 2026]},
    "Singapore": {"laps": 62, "chaos": 1.00, "years": [2018, 2019, 2022, 2023, 2024, 2025, 2026]},
    "Styria": {"laps": 71, "chaos": 0.40, "years": [2020, 2021]},
    "Turkey": {"laps": 58, "chaos": 0.60, "years": [2020, 2021]},
    "Tuscany": {"laps": 59, "chaos": 0.75, "years": [2020]},
    "USA": {"laps": 56, "chaos": 0.45, "years": [2018, 2019, 2021, 2022, 2023, 2024, 2025, 2026]}
}

# Mapeamento dos compostos de pneus para estilos visuais
def get_estilo_pneu(compound):
    styles = {
        'SOFT': {'bg': '#e10600', 'fg': '#ffffff'},
        'MEDIUM': {'bg': '#e2d014', 'fg': '#000000'},
        'HARD': {'bg': '#ffffff', 'fg': '#000000'},
        'INTERMEDIATE': {'bg': '#39b54a', 'fg': '#ffffff'},
        'WET': {'bg': '#00aeef', 'fg': '#ffffff'},
    }
    return styles.get(compound.upper(), {'bg': '#888888', 'fg': '#ffffff'})