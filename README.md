# Simple PS5 Stock Checker

This checks stock at the following sites every sixty seconds:

- Target
- Sony (direct)
- Best Buy

It only checks for the digital edition PS5. It will send a discord message
through a discord web hook with a link to buy if it finds a PS5 in stock.

To setup, simply change `sample_config.json` to `config.json`, and plug
your discord webhook in; then, run `main.py`.

```bash
mv sample_config.json config.json
# open up config.json and input your webhook url
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# this will check on an infinite loop and log to ./stock_check.log
python3 main.py
```
