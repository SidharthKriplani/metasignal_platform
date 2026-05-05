import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    return (pd,)


@app.cell
def _(pd):
    data_raw = pd.read_csv("data/raw/retailrocket/events.csv")

    data_interim = pd.read_parquet("data/interim/events_standardized.parquet")
    return data_interim, data_raw


@app.cell
def _(data_interim, data_raw):
    data_interim.shape, data_raw.shape

    # data_interim.describe(), data_raw.describe()
    return


@app.cell
def _(data):
    for i in data.columns:
        print(data[i].value_counts()*100.0/len(data))
    return


@app.cell
def _(data):
    data
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
