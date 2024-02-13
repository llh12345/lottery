

class GameInfo:
    def __init__(self, matchTime, Host, Guest, Odds: list[float], HandiCapOdds: list[float], Company: str):
        self.matchTime = matchTime
        self.Host = Host
        self.Guest = Guest
        self.Odds = Odds
        self.Handicap_num = 0.0
        # 北单的话，handiCapOdds和Odds相同
        self.Handicap_Odds = HandiCapOdds
        self.Company = Company

class BuyDecision:
    def __init__(self, game: GameInfo, amount: float, odd: float, guess: str):
        self.game = game
        self.amount = amount
        self.odd = odd
        self.guess = guess
class OddInfo:
    def __init__(self, odd, success_type, platform):
        self.odd = odd
        # 胜 平 负
        self.success_type = success_type
        # 平台
        self.platform = platform
class CompanyOdds:
    def __init__(self, CompanyName, Odds: list[float], handiCapNum):
        self.CompanyName = CompanyName
        self.Odds = Odds
        self.handiCapNum = handiCapNum

