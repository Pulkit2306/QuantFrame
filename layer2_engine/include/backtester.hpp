#pragma once
#include "order_book.hpp"
#include "strategy.hpp"
#include <memory>
#include <string>
#include <vector>

namespace qf {

struct EquityPoint {
    Nanos  ts_ns;
    double equity;
};

struct BacktestResult {
    std::string strategy_name;
    double      initial_cash;
    double      final_equity;
    double      total_return_pct;
    double      sharpe_ratio;
    double      max_drawdown_pct;
    int         total_trades;
    std::vector<EquityPoint> equity_curve;
};

class RiskManager {
public:
    explicit RiskManager(double max_position_pct = 0.1, double max_drawdown_pct = 0.2);

    // Returns false if the order should be blocked by risk limits
    bool allow(const Signal& sig, double current_equity, double peak_equity) const;

private:
    double max_position_pct_;   // max fraction of equity per trade
    double max_drawdown_pct_;   // halt trading if drawdown exceeds this
};

class Backtester {
public:
    Backtester(std::shared_ptr<Strategy> strategy,
               double initial_cash = 100'000.0);

    BacktestResult run(const std::vector<Bar>& bars);

private:
    std::shared_ptr<Strategy> strategy_;
    RiskManager               risk_;
    double                    initial_cash_;

    double cash_     = 0.0;
    double position_ = 0.0;   // shares held
    double peak_eq_  = 0.0;
    int    trades_   = 0;

    std::vector<EquityPoint> equity_curve_;

    double equity(double price) const { return cash_ + position_ * price; }
    double sharpe(const std::vector<EquityPoint>& curve) const;
    double max_drawdown(const std::vector<EquityPoint>& curve) const;
};

} // namespace qf
