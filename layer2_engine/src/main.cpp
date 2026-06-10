/*
 * QuantFrame CLI — runs a backtest from a CSV file and prints results.
 *
 * Usage:
 *   ./quantframe <csv_file> [sma|meanrev] [short_period] [long_period]
 *
 * CSV format: timestamp_ns,open,high,low,close,volume
 */

#include "backtester.hpp"
#include "strategy.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace qf {

std::vector<Bar> load_csv(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open())
        throw std::runtime_error("Cannot open: " + path);

    std::vector<Bar> bars;
    std::string line;
    std::getline(f, line); // skip header

    while (std::getline(f, line)) {
        std::istringstream ss(line);
        std::string token;
        Bar b;
        b.symbol = "UNKNOWN";

        std::getline(ss, token, ','); b.ts_ns  = std::stoll(token);
        std::getline(ss, token, ','); b.open   = std::stod(token);
        std::getline(ss, token, ','); b.high   = std::stod(token);
        std::getline(ss, token, ','); b.low    = std::stod(token);
        std::getline(ss, token, ','); b.close  = std::stod(token);
        std::getline(ss, token, ','); b.volume = std::stoll(token);
        bars.push_back(b);
    }
    return bars;
}

} // namespace qf

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0]
                  << " <bars.csv> [sma|meanrev] [short=10] [long=50]\n";
        return 1;
    }

    std::string csv_path   = argv[1];
    std::string strat_name = argc > 2 ? argv[2] : "sma";
    int short_p = argc > 3 ? std::stoi(argv[3]) : 10;
    int long_p  = argc > 4 ? std::stoi(argv[4]) : 50;

    std::vector<qf::Bar> bars;
    try {
        bars = qf::load_csv(csv_path);
    } catch (const std::exception& e) {
        std::cerr << "Error loading CSV: " << e.what() << "\n";
        return 1;
    }

    std::shared_ptr<qf::Strategy> strat;
    if (strat_name == "meanrev")
        strat = std::make_shared<qf::MeanReversionStrategy>(short_p);
    else
        strat = std::make_shared<qf::SMACrossStrategy>(short_p, long_p);

    qf::Backtester bt(strat);
    qf::BacktestResult res = bt.run(bars);

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "\n=== QuantFrame Backtest Results ===\n"
              << "Strategy    : " << res.strategy_name     << "\n"
              << "Bars loaded : " << bars.size()           << "\n"
              << "Initial $   : " << res.initial_cash      << "\n"
              << "Final $     : " << res.final_equity      << "\n"
              << "Return      : " << res.total_return_pct  << "%\n"
              << "Sharpe      : " << res.sharpe_ratio       << "\n"
              << "Max Drawdown: " << res.max_drawdown_pct  << "%\n"
              << "Trades      : " << res.total_trades      << "\n\n";

    return 0;
}
