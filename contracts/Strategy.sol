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


    uint256 public wantRateLimit = 2 *1e8;
    uint256 public rateLimitPeriod = 3600;

    uint256 public curveId;



    constructor(address _vault, uint256 _crvId) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;

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
        return string(abi.encodePacked("SingleSidedCrv", want.symbol()));
    }

    function estimatedTotalAssets() public override view returns (uint256) {
        uint256 totalCurveTokens = curveTokensInYVault().add(hCRV.balanceOf(address(this)));
        return want.balanceOf(address(this)).add(curveTokenToWant(totalCurveTokens));
    }

    // returns value of total 3pool
    function curveTokenToWant(uint256 tokens) public view returns (uint256) {

        //we want to choose lower value of virtual price and amount we really get out
        uint256 virtualOut = curvePool.get_virtual_price().mul(tokens).div(1e18);

        uint256 realOut;
        if(curveId == 0){
            realOut = curvePool.get_dy(0,1,tokens);
        } else{
            realOut = curvePool.get_dy(1,0,tokens);
        }

        return Math.min(virtualOut, realOut);
    }

    function curveTokensInYVault() public view returns (uint256) {
        uint256 balance = yvhCRV.balanceOf(address(this));
        uint256 pricePerShare = yvhCRV.getPricePerFullShare();
        return balance.mul(pricePerShare).div(10 ** yvhCRV.decimals());
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

            withdrawSome(toFree);

            wantBalance = want.balanceOf(address(this));

            if(wantBalance < _profit){
                _profit = wantBalance;
                _debtPayment = 0;
            }else if (wantBalance < _debtPayment.add(_profit)){
                _debtPayment = wantBalance.sub(_profit);
            }
        }
        
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {

        if(lastInvest.add(rateLimitPeriod) > block.timestamp ){
            return;
        }

        // Invest the rest of the want
        uint256 _wantToInvest = Math.min(want.balanceOf(address(this)), maxSingleInvest);

        if (_wantToInvest > 0) {
            //add to curve (single sided)

            if(curveId == 0){
                curvePool.add_liquidity([_wantToInvest, 0], 0);
            }else{
                curvePool.add_liquidity([0, _wantToInvest], 0);
            }
            
            //now add to yearn
            yvhCRV.depositAll();

            lastInvest = block.timestamp;
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {

        uint256 wantBal = want.balanceOf(address(this));
        if(wantBal < _amountNeeded){
            withdrawSome(_amountNeeded.sub(wantBal));
        }

        _liquidatedAmount = Math.min(_amountNeeded, want.balanceOf(address(this)));

    }

    //withdraw amount from safebox
    //safe to enter more than we have
    function withdrawSome(uint256 _amount) internal returns (uint256) {

        //how much can we withdraw
        if(curveId == 0){
            curvePool.remove_liquidity_imbalance([_amount, 0], uint256(-1));
        }else{
             curvePool.remove_liquidity_imbalance([0, _amount], uint256(-1));
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
