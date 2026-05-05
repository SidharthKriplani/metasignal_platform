# %%
from pathlib import Path

import pandas as pd


# %%
repo_root = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
events_path = repo_root / "data" / "raw" / "retailrocket" / "events.csv"


# %%
events = pd.read_csv(events_path)


# %%
events.head()


# %%
events.info()


# %%
events.describe(include="all")


# %%
events["event"].value_counts(dropna=False)
