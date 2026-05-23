# Installing DESi — the really simple guide

No Python experience needed. Follow the steps in order. Copy-paste the
commands exactly. DESi runs **offline** by default — you do **not**
need any API key to try it.

---

## Step 1 — Install Python (once)

DESi needs **Python 3.11 or newer**.

- **Windows / macOS:** download from <https://www.python.org/downloads/>
  and run the installer. On Windows, tick **"Add Python to PATH"**.
- **Linux:** it's usually already installed. If not:
  `sudo apt install python3 python3-venv` (Debian/Ubuntu).

Check it worked — open a terminal and type:

```
python --version
```

You should see `Python 3.11.x` or higher. (On macOS/Linux you may need
to type `python3` instead of `python`.)

## Step 2 — Download DESi

```
git clone https://github.com/hstre/DESi.git
```

(No git? Download the ZIP from the GitHub page, then unzip it.)

## Step 3 — Open a terminal in the DESi folder

```
cd DESi
```

## Step 4 — Create a "virtual environment" (a clean sandbox)

```
python -m venv .venv
```

Now **activate** it:

- **Windows (PowerShell):**
  ```
  .venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```
  source .venv/bin/activate
  ```

Your prompt should now start with `(.venv)`.

## Step 5 — Install DESi

```
pip install -e .
```

## Step 6 — Check everything is OK

```
desi doctor
```

You should see a list ending in **"DESi is ready for offline use."**

You can also see your settings (no secrets are ever shown):

```
desi config
```

## Step 7 — Run your first example

```
python examples/hello_desi.py
```

and a built-in command:

```
desi replay
```

That's it. 🎉 DESi is installed and running offline.

---

## Common problems

- **`desi: command not found`** → your virtual environment is not
  active. Re-run the Step 4 activate command. (Or use
  `python -m desi.governance_cli doctor`.)
- **`python: command not found`** → try `python3` instead of `python`.
- **Permission errors on Windows PowerShell** when activating → run
  `Set-ExecutionPolicy -Scope Process RemoteSigned` once, then retry.

## Want to use real LLMs later? (optional, advanced)

DESi works fully offline. Only if you *want* live model calls:

1. `cp config/desi.example.ini config/desi.local.ini`
2. Put your key under `[openrouter] api_key = ...` in
   `config/desi.local.ini` (this file is gitignored — it is never
   committed).
3. Set `offline_mode = false` and `allow_live_llm_calls = true` in the
   `[desi]` section.

Never put a real key in `desi.example.ini`. See `INSTALL.md` for more.
