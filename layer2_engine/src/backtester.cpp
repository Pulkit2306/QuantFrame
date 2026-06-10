#include "backtester.hpp"
#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace qf {

// ── RiskManager ────────────────────────────────────────────────────────────

RiskManager::RiskManager(double max_position_pct, double max_drawdown_pct)
    : max_position_pct_(max_position_pct)
    , max_drawdown_pct_(max_drawdown_pct)
{}

bool RiskManager::allow(const Signal& sig, double current_equity, double peak_equity) const {
    if (peak_equity > 0.0) {
        double dd = (peak_equity - current_equity) / peak_equity;
        if (dd > max_drawdown_pct_) return false;   // drawdown circuit breaker
    }
    return true;
}

// ── Backtester ─────────────────────────────────────────────────────────────

Backtester::Backtester(std::shared_ptr<Strategy> strategy, double initial_cash)
    : strategy_(std::move(strategy))
    , initial_cash_(initial_cash)
{}

double Backtester::sharpe(const std::vector<EquityPoint>& curve) const {
    if (curve.size() < 2) return 0.0;
    std::vector<double> returns;
    for (size_t i = 1; i < curve.size(); ++i) {
        double r = (curve[i].equity - curve[i-1].equity) / curve[i-1].equity;
        returns.push_back(r);
    }
    double mean = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double var  = 0.0;
    for (double r : returns) var += (r - mean) * (r - mean);
    double sigma = std::sqrt(var / returns.size());
    if (sigma < 1e-9) return 0.0;
    // annualized assuming daily bars
    return (mean / sigma) * std::sqrt(252.0);
}

double Backtester::max_drawdown(const std::vector<EquityPoint>& curve) const {
    double peak = 0.0, max_dd = 0.0;
    for (auto& ep : curve) {
        peak = std::max(peak, ep.equity);
        double dd = (peak - ep.equity) / peak;
        max_dd = std::max(max_dd, dd);
    }
    return max_dd * 100.0;
}

BacktestResult Backtester::run(const std::vector<Bar>& bars) {
    strategy_->reset();
    cash_     = initial_cash_;
    position_ = 0.0;
    peak_eq_  = initial_cash_;
    trades_   = 0;
    equity_curve_.clear();

    for (const auto& bar : bars) {
        double eq = equity(bar.close);
        peak_eq_ = std::max(peak_eq_, eq);
        equity_curve_.push_back({bar.ts_ns, eq});

        Signal sig = strategy_->on_bar(bar);

        if (!risk_.allow(sig, eq, peak_eq_)) continue;

        if (sig.action == Signal::Action::BUY && sig.quantity > 0) {
            double cost = sig.target_price * sig.quantity;
            if (cost <= cash_) {
                cash_     -= cost;
                position_ += sig.quantity;
                ++trades_;
            }
        } else if (sig.action == Signal::Action::SELL && position_ > 0.0) {
            double proceeds = sig.target_price * position_;
            cash_    += proceeds;
            position_ = 0.0;
            ++trades_;
        }
    }

    double final_eq = equity(bars.empty() ? 0.0 : bars.back().close);

    BacktestResult res;
    res.strategy_name    = strategy_->name();
    res.initial_cash     = initial_cash_;
    res.final_equity     = final_eq;
    res.total_return_pct = (final_eq / initial_cash_ - 1.0) * 100.0;
    res.sharpe_ratio     = sharpe(equity_curve_);
    res.max_drawdown_pct = max_drawdown(equity_curve_);
    res.total_trades     = trades_;
    res.equity_curve     = equity_curve_;
    return res;
}

} // namespace qf
