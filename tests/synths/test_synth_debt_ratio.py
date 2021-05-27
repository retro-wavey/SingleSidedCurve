import pytest
from brownie import config, Contract, Wei, chain, reverts

def test_synth_debt_ratio(vault, susd, susd_whale, yvault, curvePool, synth, cloned_strategy, gov):
    # deposit susd in vault
    susd.approve(vault, 2 ** 256 - 1, {'from': susd_whale})
    vault.deposit(Wei("10000 ether"), {'from': susd_whale})

    # harvest
    prev_pps = vault.pricePerShare()
    tx = cloned_strategy.harvest({'from': gov})
    chain.sleep(360+1) # 6 mins
    chain.mine()
    assert synth.balanceOf(cloned_strategy) > 0
    assert yvault.balanceOf(cloned_strategy) == 0
    tx = cloned_strategy.harvest({'from': gov})
    assert yvault.balanceOf(cloned_strategy) > 0
    assert synth.balanceOf(cloned_strategy) == 0

    vault.updateStrategyDebtRatio(cloned_strategy, 0, {'from': gov})

    # if we don't uninvest manually, the strategy cannot withdraw
    with reverts():
        cloned_strategy.harvest({'from': gov})

    cloned_strategy.manualRemoveFullLiquidity({'from': gov})
    chain.sleep(360 + 1)
    chain.mine(1)
    assert synth.balanceOf(cloned_strategy) == 0
    assert susd.balanceOf(cloned_strategy) > 0
    assert yvault.balanceOf(cloned_strategy) == 0
    tx = cloned_strategy.harvest({'from': gov})
    assert synth.balanceOf(cloned_strategy) == 0
    assert susd.balanceOf(cloned_strategy) > 0
    assert yvault.balanceOf(cloned_strategy) < 10_000 # dust set

