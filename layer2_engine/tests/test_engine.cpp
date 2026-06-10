#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "order_book.hpp"
#include "strategy.hpp"
#include "backtester.hpp"
#include <memory>

using namespace qf;

// ── Order Book Tests ────────────────────────────────────────────────────────

TEST_CASE("OrderBook: best quote after adding orders") {
    OrderBook book("AAPL");
    book.add_order({1, "AAPL", Side::BID, 150.0, 100, now_ns()});
    book.add_order({2, "AAPL", Side::ASK, 151.0, 100, now_ns()});

    auto q = book.best_quote();
    REQUIRE(q.has_value());
    CHECK(q->bid == doctest::Approx(150.0));
    CHECK(q->ask == doctest::Approx(151.0));
}

TEST_CASE("OrderBook: cancel removes order from book") {
    OrderBook book("MSFT");
    book.add_order({1, "MSFT", Side::BID, 200.0, 500, now_ns()});
    book.cancel_order(1);

    auto q = book.best_quote();
    CHECK_FALSE(q.has_value());
}

TEST_CASE("OrderBook: match executes trade") {
    OrderBook book("SPY");
    book.add_order({1, "SPY", Side::ASK, 450.0, 100, now_ns()});

    Order taker{2, "SPY", Side::BID, 451.0, 50, now_ns()};
    auto trades = book.match(taker);

    REQUIRE(trades.size() == 1);
    CHECK(trades[0].price    == doctest::Approx(450.0));
    CHECK(trades[0].quantity == 50);
}

TEST_CASE("OrderBook: partial fill leaves remainder") {
    OrderBook book("QQQ");
    book.add_order({1, "QQQ", Side::ASK, 300.0, 100, now_ns()});

    Order taker{2, "QQQ", Side::BID, 300.0, 60, now_ns()};
    auto trades = book.match(taker);

    CHECK(trades[0].quantity == 60);
    auto asks = book.asks(1);
    REQUIRE(asks.size() == 1);
    CHECK(asks[0].second == 40);  // 100 - 60 remaining
}

// ── Strategy Tests ──────────────────────────────────────────────────────────

TEST_CASE("SMACrossStrategy: holds during warmup") {
    SMACrossStrategy strat(5, 10);
    Bar bar{"AAPL", now_ns(), 100, 101, 99, 100, 1000};
    Signal sig = strat.on_bar(bar);
    CHECK(sig.action == Signal::Action::HOLD);
}

TEST_CASE("SMACrossStrategy: invalid periods throw") {
    CHECK_THROWS(SMACrossStrategy(10, 5));
}

// ── Backtester Tests ────────────────────────────────────────────────────────

TEST_CASE("Backtester: result fields populated") {
    auto strat = std::make_shared<SMACrossStrategy>(5, 10);
    Backtester bt(strat, 100000.0);

    std::vector<Bar> bars;
    for (int i = 0; i < 20; ++i) {
        double price = 100.0 + i;
        bars.push_back({"AAPL", now_ns() + i * 86400LL * 1'000'000'000LL,
                        price, price + 1, price - 1, price, 1000000});
    }

    auto res = bt.run(bars);
    CHECK(res.initial_cash == doctest::Approx(100000.0));
    CHECK(res.equity_curve.size() == bars.size());
    CHECK(!res.strategy_name.empty());
}
