from itertools import count
from brownie import Wei, Contract, interface, accounts, chain
import eth_abi
import random
import brownie


def ssc_ib():
    safe = ApeSafe("brain.ychad.eth")
    vault = safe.contract("0xa354F35829Ae975e850e23e9615b11Da1B3dC4DE") # v0.4.3
    vault_old = safe.contract("0x5f18C75AbDAe578b483E5F43f12a39cF75b973a9") # v0.3.0
    ssc = safe.contract("0x0c8f62939Aeee6376f5FAc88f48a5A3F2Cf5dEbB")
    ssc_old = safe.contract("0x80af28cb1e44C44662F144475d7667C9C0aaB3C3")
    router = safe.contract("0x36822d0b11F4594380181cE6e76bd4986d46c389")
    flash_mint = safe.contract("0xd4E94061183b2DBF24473F28A3559cf4dE4459Db")
    gen_lev = safe.contract("0x342491C093A640c7c2347c4FFA7D8b9cBC84D1EB")
    currency = safe.contract(vault.token())
    decimals = currency.decimals()

    # STEP 1: Configure debt ratios on old vault
    debt_old_ssc = vault_old.strategies(ssc_old).dict()["totalDebt"]
    actual_old_ssc_ratio = int(debt_old_ssc / vault_old.totalAssets() * 10_000)
    debt_router = vault_old.strategies(router).dict()["totalDebt"]

    vault_old.updateStrategyDebtRatio(ssc_old, 0)
    available_ratio = 10_000 - vault_old.debtRatio() - 25 # Keep 25 bps free for cheap withdraws
    vault_old.updateStrategyDebtRatio(router, available_ratio)
    print("-------")
    
    # STEP 2: Harvest old SSC and router and check results
    tx = ssc_old.harvest()
    print("Gain ---->",tx.events["Harvested"]["profit"]/1e6) # Gain ----> 40520.57394
    print("Loss ---->",tx.events["Harvested"]["loss"]/1e6) #Loss ----> 0.0
    print("Old ssc remaining debt/assets", vault_old.strategies(ssc_old).dict()["totalDebt"]/1e6, ssc_old.estimatedTotalAssets()/1e6) # Old ssc remaining debt/assets 0.0 3622.550984
    assert vault_old.strategies(ssc_old).dict()["totalDebt"] == 0
    if ssc_old.estimatedTotalAssets() > 3_000 * 1e6: # Not all money may be freed. Lets harvest again if there's still $3k available
        tx = ssc_old.harvest()
    assert ssc_old.estimatedTotalAssets() < 1_000  * 1e6
    r_before = router.estimatedTotalAssets()
    router.harvest()
    r_after = router.estimatedTotalAssets()
    router_debt_gain = (r_after - r_before)
    print("old ssc debt before",debt_old_ssc/1e6) # old ssc debt before 39181594.544272
    print("router debt gain after", router_debt_gain/1e6) # router debt gain after 37023157.841019
    print("-------")

    # STEP 3: Configure debt ratios on new vault
    actual_ratio_of_free_assets = int(currency.balanceOf(vault)/vault.totalAssets()*10_000)
    remainder_ratio = 10_000 - actual_ratio_of_free_assets
    gen_lev_ratio_current = vault.strategies(gen_lev).dict()["totalDebt"] / 10_000
    gen_lev_ratio = int(remainder_ratio * gen_lev_ratio_current)
    flash_mint_ratio = remainder_ratio - gen_lev_ratio # Flashmint + genlev are the only two strats with ratio currently
    print("actual ratio of free assets",actual_ratio_of_free_assets) # actual ratio of free assets 4440
    vault.updateStrategyDebtRatio(gen_lev, gen_lev_ratio)
    vault.updateStrategyDebtRatio(flash_mint, flash_mint_ratio)
    vault.updateStrategyDebtRatio(ssc, actual_ratio_of_free_assets)
    print("total debt ratio", vault.debtRatio()) # total debt ratio 10000
    print("-------")

    # STEP 4: Harvest debt into new SSC and check
    ssc.updateMaxSingleInvest(200_000_000 * 1e6) # We need to allow a huge investment
    ssc.harvest({"from": gov})
    ssc.updateMaxSingleInvest(3_000_000 * 1e6) # Set this back after using
    ssc_debt = vault.strategies(ssc).dict()["totalDebt"]
    ssc_assets = ssc.estimatedTotalAssets()
    print("new ssc debt", ssc_debt/1e6) # new ssc debt 38368386.104782
    print("new ssc assets", ssc_assets/1e6) # new ssc assets 38355953.446487
    print("Did we take a loss on deposit?", ssc_debt > ssc_assets, (ssc_assets - ssc_debt)/1e6) # Did we take a loss on deposit? False 38354316.174432
    print("-------")

    # STEP 5: Check that we left other strategies on the vault with enough assets
    gen_lev_debt_on_harvest = gen_lev_ratio * vault.totalAssets() / 10_000
    gen_lev_current_debt = vault.strategies(gen_lev).dict()["totalDebt"]

    flash_mint_debt_on_harvest = flash_mint_ratio * vault.totalAssets() / 10_000
    flash_mint_current_debt = vault.strategies(flash_mint).dict()["totalDebt"]

    print(gen_lev_debt_on_harvest / 1e6, gen_lev_current_debt / 1e6) # 30262631.895122975 31491061.664283
    print(flash_mint_debt_on_harvest / 1e6 , flash_mint_current_debt / 1e6) # 17784265.117122523 16555644.620477
    
    assert gen_lev_debt_on_harvest >= gen_lev_current_debt - (1_500_000 * 1e6) # Give some buffer
    assert flash_mint_debt_on_harvest >= flash_mint_current_debt - (1_500_000 * 1e6)

    safe_tx = safe.multisend_from_receipts()
    safe_tx.sign(get_signer().private_key)
    safe.preview(safe_tx, events=False, call_trace=False)
    safe.post_transaction(safe_tx)