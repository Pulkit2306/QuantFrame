#include "order_book.hpp"
#include <stdexcept>

namespace qf {

OrderBook::OrderBook(std::string symbol) : symbol_(std::move(symbol)) {}

void OrderBook::add_order(const Order& o) {
    std::lock_guard<std::mutex> lk(mu_);
    orders_[o.id] = o;
    if (o.side == Side::BID)
        bids_[o.price] += o.quantity;
    else
        asks_[o.price] += o.quantity;
    order_count.fetch_add(1, std::memory_order_relaxed);
}

void OrderBook::cancel_order(uint64_t order_id) {
    std::lock_guard<std::mutex> lk(mu_);
    auto it = orders_.find(order_id);
    if (it == orders_.end()) return;

    const Order& o = it->second;
    if (o.side == Side::BID) {
        bids_[o.price] -= o.quantity;
        if (bids_[o.price] <= 0) bids_.erase(o.price);
    } else {
        asks_[o.price] -= o.quantity;
        if (asks_[o.price] <= 0) asks_.erase(o.price);
    }
    orders_.erase(it);
}

std::vector<Trade> OrderBook::match(const Order& taker) {
    std::lock_guard<std::mutex> lk(mu_);
    std::vector<Trade> trades;
    Volume remaining = taker.quantity;

    if (taker.side == Side::BID) {
        // taker is buying — match against best asks
        for (auto it = asks_.begin(); it != asks_.end() && remaining > 0; ) {
            if (taker.price < it->first) break;  // price not aggressive enough
            Volume fill = std::min(remaining, it->second);
            trades.push_back({0, taker.id, it->first, fill, now_ns()});
            remaining     -= fill;
            it->second    -= fill;
            if (it->second == 0) it = asks_.erase(it);
            else ++it;
        }
    } else {
        // taker is selling — match against best bids
        for (auto it = bids_.begin(); it != bids_.end() && remaining > 0; ) {
            if (taker.price > it->first) break;
            Volume fill = std::min(remaining, it->second);
            trades.push_back({0, taker.id, it->first, fill, now_ns()});
            remaining     -= fill;
            it->second    -= fill;
            if (it->second == 0) it = bids_.erase(it);
            else ++it;
        }
    }
    return trades;
}

std::optional<Quote> OrderBook::best_quote() const {
    std::lock_guard<std::mutex> lk(mu_);
    if (bids_.empty() || asks_.empty()) return std::nullopt;
    return Quote{
        bids_.begin()->first,  asks_.begin()->first,
        bids_.begin()->second, asks_.begin()->second,
    };
}

std::vector<std::pair<Price, Volume>> OrderBook::bids(int depth) const {
    std::lock_guard<std::mutex> lk(mu_);
    std::vector<std::pair<Price, Volume>> out;
    int n = 0;
    for (auto& [p, v] : bids_) {
        if (n++ >= depth) break;
        out.emplace_back(p, v);
    }
    return out;
}

std::vector<std::pair<Price, Volume>> OrderBook::asks(int depth) const {
    std::lock_guard<std::mutex> lk(mu_);
    std::vector<std::pair<Price, Volume>> out;
    int n = 0;
    for (auto& [p, v] : asks_) {
        if (n++ >= depth) break;
        out.emplace_back(p, v);
    }
    return out;
}

} // namespace qf
