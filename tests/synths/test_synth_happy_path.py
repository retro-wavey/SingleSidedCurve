import pytest
from brownie import config, Contract, Wei, chain

def test_synth_happy_path(vault, susd, susd_whale, yvault, curvePool, synth, cloned_strategy, gov):
    print("yVault", yvault)
    print("CurvePool", curvePool)
    print("Synth", synth)
    
    # deposit susd in vault
    susd.approve(vault, 2 ** 256 - 1, {'from': susd_whale})
    vault.deposit(Wei("10000 ether"), {'from': susd_whale})

    # harvest 
    # first harvest will only invest sUSD in sETH
    # afterwards, both actions will be done
    prev_pps = vault.pricePerShare()
    tx = cloned_strategy.harvest({'from': gov})
    assert yvault.balanceOf(cloned_strategy) == 0
    assert synth.balanceOf(cloned_strategy) > 0
    assert susd.balanceOf(cloned_strategy) > 0 
    assert susd.balanceOf(cloned_strategy) == vault.strategies(cloned_strategy).dict()['totalDebt'] * 0.1

    chain.sleep(360 + 1) # over 6 mins 
    chain.mine(1)
    tx = cloned_strategy.harvest({'from': gov})
    # chain.sleep(360 + 1) # over 6 mins 
    # chain.mine(1)
    assert yvault.balanceOf(cloned_strategy) > 0
    assert synth.balanceOf(cloned_strategy) == 0
    assert susd.balanceOf(cloned_strategy) == vault.strategies(cloned_strategy).dict()['totalDebt'] * 0.1

    # TODO: generate revenue to force the strategy to take profit

    tx = cloned_strategy.harvest({'from': gov})

    assert False 