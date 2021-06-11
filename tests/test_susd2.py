from brownie import Wei, reverts, Contract, accounts, chain


def test_susd2(zap_strategy):
    strategy = zap_strategy
    vault = Contract(strategy.vault())
    gov = accounts.at(vault.governance(), True)
    vault = Contract(strategy.vault(), owner=gov)
    susd = Contract(vault.token())

    s1 = Contract(vault.withdrawalQueue(1))
    s1_debt_ratio = vault.strategies(s1).dict()['debtRatio']
    vault.revokeStrategy(s1)
    s1.harvest({"from": gov})

    vault.addStrategy(strategy, s1_debt_ratio, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    strategy.harvest({"from": gov})

    assert vault.strategies(strategy).dict()["totalDebt"] > 0

    vault.revokeStrategy(strategy)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == 0
