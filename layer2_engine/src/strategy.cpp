#include "strategy.hpp"
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace qf {

// ── SMA Crossover ──────────────────────────────────────────────────────────

SMACrossStrategy::SMACrossStrategy(int short_period, int long_period)
    : Strategy("SMA_" + std::to_string(short_period) + "_" + std::to_string(long_period))
    , short_period_(short_period)
    , long_period_(long_period)
{
    if (short_period >= long_period)
        throw std::invalid_argument("short_period must be < long_period");
}

double SMACrossStrategy::sma(int period) const {
    if (static_cast<int>(prices_.size()) < period) return 0.0;
    double sum = 0.0;
    auto it = prices_.end() - period;
    for (int i = 0; i < period; ++i) sum += *it++;
    return sum / period;
}

Signal SMACrossStrategy::on_bar(const Bar& bar) {
    prices_.push_back(bar.close);
    if (static_cast<int>(prices_.size()) < long_period_)
        return {Signal::Action::HOLD, 0, 0, "warming up"};

    double s = sma(short_period_);
    double l = sma(long_period_);

    if (s > l && position_ == 0.0) {
        double qty = std::floor(cash_ / bar.close);
        return {Signal::Action::BUY, bar.close, static_cast<int64_t>(qty), "short SMA > long SMA"};
    }
    if (s < l && position_ > 0.0) {
        return {Signal::Action::SELL, bar.close, static_cast<int64_t>(position_), "short SMA < long SMA"};
    }
    return {Signal::Action::HOLD, 0, 0, ""};
}

void SMACrossStrategy::reset() {
    prices_.clear();
    position_ = 0.0;
    cash_ = 100'000.0;
}

// ── Mean Reversion ─────────────────────────────────────────────────────────

MeanReversionStrategy::MeanReversionStrategy(int period, double z_thresh)
    : Strategy("MeanReversion_" + std::to_string(period))
    , period_(period)
    , z_thresh_(z_thresh)
{}

Signal MeanReversionStrategy::on_bar(const Bar& bar) {
    prices_.push_back(bar.close);
    if (static_cast<int>(prices_.size()) < period_)
        return {Signal::Action::HOLD, 0, 0, "warming up"};

    // rolling mean and std over last `period_` bars
    auto begin = prices_.end() - period_;
    double mean = std::accumulate(begin, prices_.end(), 0.0) / period_;
    double var  = 0.0;
    for (auto it = begin; it != prices_.end(); ++it)
        var += (*it - mean) * (*it - mean);
    double sigma = std::sqrt(var / period_);
    if (sigma < 1e-9) return {Signal::Action::HOLD, 0, 0, ""};

    double z = (bar.close - mean) / sigma;

    if (z < -z_thresh_ && position_ == 0.0) {
        double qty = std::floor(cash_ / bar.close);
        return {Signal::Action::BUY, bar.close, static_cast<int64_t>(qty),
                "z=" + std::to_string(z)};
    }
    if (z > z_thresh_ && position_ > 0.0) {
        return {Signal::Action::SELL, bar.close, static_cast<int64_t>(position_),
                "z=" + std::to_string(z)};
    }
    return {Signal::Action::HOLD, 0, 0, ""};
}

void MeanReversionStrategy::reset() {
    prices_.clear();
    position_ = 0.0;
    cash_ = 100'000.0;
}

} // namespace qf
