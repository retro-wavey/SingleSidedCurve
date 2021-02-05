// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./interfaces/curve/Curve.sol";
import "./interfaces/curve/Gauge.sol";
import "./interfaces/curve/IMinter.sol";
import "./interfaces/curve/ICrvV3.sol";
import "./interfaces/Yearn/IVaultV1.sol";
import "./interfaces/UniswapInterfaces/IUniswapV2Router02.sol";

// These are the core Yearn libraries
import {
    BaseStrategy
} from "@yearnvaults/contracts/BaseStrategy.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";



// Import interfaces for many popular DeFi projects, or add your own!
//import "../interfaces/<protocol>/<Interface>.sol";

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address private uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    ICurveFi public curvePool =  ICurveFi(address(0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F));
    ICrvV3 public hCRV = ICrvV3(address(0xb19059ebb43466C323583928285a49f558E572Fd));

    address public constant weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);

    IVaultV1 public yvhCRV = IVaultV1(address(0x46AFc2dfBd1ea0c0760CAD8262A5838e803A37e5));

    uint256 public lastInvest = 0;
    uint256 public minTimePerInvest = 3600;
    uint256 public maxSingleInvest = 2*1e18; // 2 hbtc per hour default
    uint256 public slippageProtection = 50; //out of 10000. 50 = 0.5%
    uint256 public constant DENOMINATOR = 10000;


    int128 public curveId;



    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
         maxReportDelay = 6300;
        profitFactor = 1500;
        debtThreshold = 100*1e18;

        want.safeApprove(address(curvePool), uint256(-1));
        hCRV.approve(address(yvhCRV), uint256(-1));

        if(curvePool.coins(0) == address(want)){
            curveId =0;
        }else if ( curvePool.coins(1) == address(want)){
            curveId =1;
        }else{
            require(false, "Coin not found");
        }
    }


    function name() external override view returns (string memory) {
        // Add your own name here, suggestion e.g. "StrategyCreamYFI"
        return string(abi.encodePacked("SingleSidedCrv"));
    }

    function updateMinTimePerInvest(uint256 _minTimePerInvest) public onlyGovernance {
        minTimePerInvest = _minTimePerInvest;
    }
    function updateMaxSingleInvest(uint256 _maxSingleInvest) public onlyGovernance {
        maxSingleInvest = _maxSingleInvest;
    }
    function updateSlippageProtection(uint256 _slippageProtection) public onlyGovernance {
        slippageProtection = _slippageProtection;
    }

    function estimatedTotalAssets() public override view returns (uint256) {
        uint256 totalCurveTokens = curveTokensInYVault().add(hCRV.balanceOf(address(this)));
        return want.balanceOf(address(this)).add(curveTokenToWant(totalCurveTokens));
    }

    // returns value of total 3pool
    function curveTokenToWant(uint256 tokens) public view returns (uint256) {
        if(tokens == 0){
            return 0;
        }

        //we want to choose lower value of virtual price and amount we really get out
        //this means we will always underestimate current assets. 
        uint256 virtualOut = curvePool.get_virtual_price().mul(tokens).div(1e18);

        uint256 realOut = curvePool.calc_withdraw_one_coin(tokens, curveId);

        return Math.min(virtualOut, realOut);
        //return realOut;
    }

    function curveTokensInYVault() public view returns (uint256) {
        uint256 balance = yvhCRV.balanceOf(address(this));

        if(yvhCRV.totalSupply() == 0){
            //needed because of revert on priceperfullshare if 0
            return 0;
        }
        uint256 pricePerShare = yvhCRV.getPricePerFullShare();
        return balance.mul(pricePerShare).div(1e18);
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {

        _debtPayment = _debtOutstanding;

        uint256 debt = vault.strategies(address(this)).totalDebt;
        uint256 currentValue = estimatedTotalAssets();
        uint256 wantBalance = want.balanceOf(address(this));


        if(debt < currentValue){
            //profit
            _profit = currentValue.sub(debt);
        }else{
            _loss = debt.sub(currentValue);
        }

        uint256 toFree = _debtPayment.add(_profit);

        if(toFree > wantBalance){
            toFree = toFree.sub(wantBalance);

            (, uint256 withdrawalLoss) = withdrawSome(toFree);

            //when we withdraw we can lose money in the withdrawal
            if(withdrawalLoss < _profit){
                _profit = _profit.sub(withdrawalLoss);

            }else{
                _loss = _loss.add(withdrawalLoss.sub(_profit));
                _profit = 0;
            }

            wantBalance = want.balanceOf(address(this));

            if(wantBalance < _profit){
                _profit = wantBalance;
                _debtPayment = 0;
            }else if (wantBalance < _debtPayment.add(_profit)){
                _debtPayment = wantBalance.sub(_profit);
            }
        }
        
    }

    function tendTrigger(uint256 callCost) public override view returns (bool) {

        uint256 wantBal = want.balanceOf(address(this));
        uint256 _wantToInvest = Math.min(wantBal, maxSingleInvest);

        if(lastInvest.add(minTimePerInvest) < block.timestamp &&  _wantToInvest > 1 && _checkSlip(_wantToInvest)){
            return true;
        }
    }

    function _checkSlip(uint256 _wantToInvest) private view returns (bool){
        uint256 expectedOut = _wantToInvest.mul(1e18).div(curvePool.get_virtual_price());
        uint256 maxSlip = expectedOut.mul(DENOMINATOR.sub(slippageProtection)).div(DENOMINATOR);

        uint256[2] memory amounts; 

        if(curveId == 0){
            amounts = [_wantToInvest, 0];
        }else{
            amounts = [0, _wantToInvest];
        }

        uint256 roughOut = curvePool.calc_token_amount(amounts, true);

        if(roughOut >= maxSlip){
            return true;
        }
    }


    function adjustPosition(uint256 _debtOutstanding) internal override {

        if(lastInvest.add(minTimePerInvest) > block.timestamp ){
            return;
        }

        // Invest the rest of the want
        uint256 _wantToInvest = Math.min(want.balanceOf(address(this)), maxSingleInvest);

        if (_wantToInvest > 0) {
            //add to curve (single sided)

            uint256[2] memory amounts; 

            if(curveId == 0){
                amounts = [_wantToInvest, 0];
            }else{
                amounts = [0, _wantToInvest];
            }

           
            if(_checkSlip(_wantToInvest)){
                curvePool.add_liquidity(amounts, 0);
                //now add to yearn
                yvhCRV.depositAll();

                lastInvest = block.timestamp;
            }

        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {

        uint256 wantBal = want.balanceOf(address(this));
        if(wantBal < _amountNeeded){
            (_liquidatedAmount, _loss) = withdrawSome(_amountNeeded.sub(wantBal));
        }

        _liquidatedAmount = Math.min(_amountNeeded, _liquidatedAmount.add(wantBal));

    }

    //safe to enter more than we have
    function withdrawSome(uint256 _amount) internal returns (uint256 _liquidatedAmount, uint256 _loss) {

        uint256 wantBalanceBefore = want.balanceOf(address(this));

        //let's take the amount we need if virtual price is real. Let's add the 
        uint256 virtualPrice = curvePool.get_virtual_price();
        uint256 amountWeNeedFromVirtualPrice = _amount.mul(1e18).div(virtualPrice);

        uint256 crvBeforeBalance = hCRV.balanceOf(address(this)); //should be zero but just incase...

        uint256 pricePerFullShare = yvhCRV.getPricePerFullShare();
        uint256 amountFromVault = amountWeNeedFromVirtualPrice.mul(1e18).div(pricePerFullShare);
        

        if(amountFromVault > yvhCRV.balanceOf(address(this))){
            amountFromVault = yvhCRV.balanceOf(address(this));
            //this is not loss. so we amend amount

            uint256 _amountOfCrv = amountFromVault.mul(pricePerFullShare).div(1e18);
            _amount = _amountOfCrv.mul(virtualPrice).div(1e18);
        }

        yvhCRV.withdraw(_amount);
        uint256 toWithdraw = hCRV.balanceOf(address(this)).sub(crvBeforeBalance);
 
        curvePool.remove_liquidity_one_coin(toWithdraw, curveId, toWithdraw.mul(DENOMINATOR.sub(slippageProtection)).div(DENOMINATOR));

        uint256 diff = want.balanceOf(address(this)).sub(wantBalanceBefore);

        if(diff > _amount){
            _liquidatedAmount = _amount;
        }else{
            _liquidatedAmount = diff;
            _loss = _amount.sub(diff);
        }

    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        yvhCRV.transfer(_newStrategy, yvhCRV.balanceOf(address(this)));
    }

    


    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    // NOTE: Do *not* include `want`, already included in `sweep` below
    //
    // Example:
    //
    //    function protectedTokens() internal override view returns (address[] memory) {
    //      address[] memory protected = new address[](3);
    //      protected[0] = tokenA;
    //      protected[1] = tokenB;
    //      protected[2] = tokenC;
    //      return protected;
    //    }
    function protectedTokens()
        internal
        override
        view
        returns (address[] memory)
    {

        address[] memory protected = new address[](1);
          protected[0] = address(yvhCRV);
    
          return protected;
    }
}
