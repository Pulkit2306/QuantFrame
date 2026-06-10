#pragma once
#include "order_book.hpp"
#include <string>
#include <vector>

namespace qf {

struct Bar {
    std::string symbol;
    Nanos       ts_ns;
    double      open, high, low, close;
    int64_t     volume;
};

struct Signal {
    enum class Action { BUY, SELL, HOLD };
    Action  action;
    double  target_price;
    int64_t quantity;
    std::string reason;
};

/*
 * Abstract base strategy — plug in a subclass to the backtesting engine.
 * The OOP design lets you swap strategies without touching the engine.
 */
class Strategy {
public:
    explicit Strategy(std::string name) : name_(std::move(name)) {}
    virtual ~Strategy() = default;

    virtual Signal on_bar(const Bar& bar) = 0;
    virtual void   on_trade(const Trade& t) {}
    virtual void   reset() {}

    const std::string& name() const { return name_; }

protected:
    std::string name_;
    double      position_ = 0.0;
    double      cash_     = 100'000.0;
};

// ── Built-in strategies ─────────────────────────────────────────────────────

/*
 * Simple Moving Average Crossover:
 * BUY when short SMA crosses above long SMA, SELL when it crosses below.
 * Classic trend-following signal used as a benchmark.
 */
class SMACrossStrategy : public Strategy {
public:
    SMACrossStrategy(int short_period, int long_period);
    Signal on_bar(const Bar& bar) override;
    void   reset() override;

private:
    int short_period_, long_period_;
    std::vector<double> prices_;
    double sma(int period) const;
};

/*
 * Mean Reversion (Bollinger Bands):
 * BUY when price drops 2σ below mean, SELL when 2σ above.
 */
class MeanReversionStrategy : public Strategy {
public:
    explicit MeanReversionStrategy(int period = 20, double z_thresh = 2.0);
    Signal on_bar(const Bar& bar) override;
    void   reset() override;

private:
    int    period_;
    double z_thresh_;
    std::vector<double> prices_;
};

} // namespace qf
