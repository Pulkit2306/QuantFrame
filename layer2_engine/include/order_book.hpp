#pragma once
#include <atomic>
#include <cstdint>
#include <functional>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

namespace qf {

using Price  = double;
using Volume = int64_t;
using Nanos  = int64_t;

inline Nanos now_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return static_cast<Nanos>(ts.tv_sec) * 1'000'000'000LL + ts.tv_nsec;
}

enum class Side : uint8_t { BID, ASK };

struct Order {
    uint64_t    id;
    std::string symbol;
    Side        side;
    Price       price;
    Volume      quantity;
    Nanos       ts_ns;   // nanosecond-resolution timestamp
};

struct Trade {
    uint64_t maker_id;
    uint64_t taker_id;
    Price    price;
    Volume   quantity;
    Nanos    ts_ns;
};

struct Quote {
    Price  bid;
    Price  ask;
    Volume bid_size;
    Volume ask_size;
};

/*
 * Lock-free order book using per-side mutexes.
 * In a production HFT system this would use a lock-free skip list or
 * a flat price-level array. For a backtester, std::map gives O(log n)
 * insert/erase with iterator stability — good enough and auditable.
 */
class OrderBook {
public:
    explicit OrderBook(std::string symbol);

    void add_order(const Order& o);
    void cancel_order(uint64_t order_id);
    std::vector<Trade> match(const Order& taker);

    std::optional<Quote> best_quote() const;
    std::vector<std::pair<Price, Volume>> bids(int depth = 5) const;
    std::vector<std::pair<Price, Volume>> asks(int depth = 5) const;

    const std::string& symbol() const { return symbol_; }
    std::atomic<uint64_t> order_count{0};

private:
    std::string symbol_;

    // price -> total volume at that level
    std::map<Price, Volume, std::greater<Price>> bids_;  // descending
    std::map<Price, Volume>                      asks_;  // ascending

    // order_id -> Order for cancellation
    std::map<uint64_t, Order> orders_;

    mutable std::mutex mu_;
};

} // namespace qf
