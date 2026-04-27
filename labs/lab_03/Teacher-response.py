'''
Elizabeth,

CHAT SUMMARY
You did a strong job using AI as a design partner rather than just asking it for code.

You consistently restated the goal before coding and asked for ambiguities to be resolved first.
You clearly defined State, Transitions, and Invariants for each file before implementation.
You made decisions about ordering (carry forward → splits → transactions), which shows real control of the system design.

This is exactly the kind of process the assignment is trying to develop.

The main area for improvement is that AI is still doing most of the architectural work, especially in shaping the final structure of each file. 
You are guiding the process, but you are not always the one proposing the structure first.

How to improve:

Before asking AI, try to propose your own structure first (even if imperfect).
Push AI more with: “Here is my design—what’s wrong with it?” instead of “What should I do?”

Overall, this is a strong submission that shows good control, but not complete ownership of the design.


CODE SUMMARY
You built a solid system with clear separation of responsibilities, and parts of your implementation are very strong.

What you did well
build_stocks_by_date.py is well structured:
Correct transition order (carry forward → splits → transactions)
Proper handling of average cost and splits
One snapshot per market date
build_cash_by_date.py is thoughtfully designed:
Uses prior-day positions for dividends, which is correct
build_portfolio_by_date.py is clean:
Good separation of helpers (price lookup, row building, printing, saving)
Clear and readable structure

These pieces show a strong understanding of state transitions over time.

Main issue (important)

Your transaction design is inconsistent, especially around cash.

Contributions and withdrawals use:

{"type": "...", "amount": ...}
Buy/sell transactions affect cash indirectly
There are no explicit $$$$ cash transactions

This means:
transactions.json is not a complete source of truth

Instead, cash is reconstructed later in build_cash_by_date.py.

In this assignment, the intended design is:

Cash is treated like a security:
ticker = "$$$$"
price = 1.0
Every buy/sell should have a matching cash transaction
Why this matters

Right now:

You have two representations of cash:
"amount" (contribution/withdrawal)
computed flows (buy/sell/dividends)

This creates:

inconsistency
harder debugging
weaker system design
How to improve

Unify everything under one model:

Represent cash as:

{"ticker": "$$$$", "shares": ..., "price": 1.0}
For every:
buy → add matching $$$$ withdrawal
sell → add matching $$$$ contribution

Then:

transactions.json becomes the complete ledger
downstream functions become simpler and more consistent
Minor notes
Good use of helper functions and structure
Clear naming and readable flow
Strong separation between computation and display
Overall Summary

You clearly understand how to build a system that evolves over time, and your derived-state functions (stocks, cash, portfolio) are strong.

GRADE A

The main gap is in the core transaction design, which should be the foundation of the entire system.

Fixing that would significantly improve both correctness and clarity.
