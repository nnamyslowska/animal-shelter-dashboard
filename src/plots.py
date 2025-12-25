import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def plot_bar_counts(
    counts: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str = "Count",
    top_n: int | None = 12,
    figsize=(1, 3),
    cmap_name: str = "viridis"
):
    counts = counts.dropna()

    if top_n is not None and len(counts) > top_n:
        counts = counts.iloc[:top_n]

    counts = counts.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=figsize)

    cmap = plt.get_cmap(cmap_name)
    colors = [cmap(i) for i in range(len(counts))]

    ax.bar(counts.index.astype(str), counts.values, color=colors)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()

    return fig

def plot_hist(
    series: pd.Series,
    title: str,
    xlabel: str,
    bins: int = 30,
    ylabel: str = "Frequency",
    figsize=(6.5, 3.4)
):
    data = series.dropna()

    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(data, bins=bins)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()

    return fig

def plot_line(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: tuple = (6.5, 3.2),
    color=None,
    date_format: bool = False,
    month_interval: int = 6
):
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(df[x], df[y], color=color or plt.cm.viridis(0.25))

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)

    if date_format:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=month_interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=35, ha="right")

    plt.tight_layout()
    return fig

def plot_scatter(
    df,
    x: str,
    y: str,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize=(6.5, 3.2),
    alpha: float = 0.35
):
    fig, ax = plt.subplots(figsize=figsize)

    d = df[[x, y]].dropna()
    ax.scatter(d[x], d[y], alpha=alpha)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)

    plt.tight_layout()
    return fig


def plot_box(
    df,
    value_col: str,
    group_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    top_n: int = 6,
    figsize=(7, 3.6),
    y_max: int | None = None 
):
    d = df[[value_col, group_col]].dropna()

    top_groups = d[group_col].value_counts().head(top_n).index
    d = d[d[group_col].isin(top_groups)]

    groups = [d.loc[d[group_col] == g, value_col].values for g in top_groups]

    fig, ax = plt.subplots(figsize=figsize)
    ax.boxplot(groups, labels=[str(g) for g in top_groups], showfliers=False)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)

    plt.xticks(rotation=35, ha="right")

    if y_max is not None:
        ax.set_ylim(0, y_max)

    plt.tight_layout()
    return fig


def plot_stacked_bar(
    df: pd.DataFrame,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize=(6.5, 3.4),
    cmap_name: str = "viridis",
    legend_title: str = "Category"
):
    def clean_label(v) -> str:
        if isinstance(v, tuple) and len(v) > 0:
            return str(v[0])

        s = str(v).strip()
        if s.startswith("(") and s.endswith(")") and "," in s:
            inner = s[1:-1]
            first = inner.split(",")[0].strip().strip("'").strip('"')
            return first

        return s

    df_plot = df.copy()
    df_plot.index = [clean_label(i) for i in df_plot.index]
    df_plot = df_plot.groupby(df_plot.index).sum()

    fig, ax = plt.subplots(figsize=figsize)
    df_plot.plot(kind="bar", stacked=True, ax=ax, colormap=cmap_name)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)

    ax.legend(title=legend_title, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()

    return fig

def plot_violin_by_group(
    df: pd.DataFrame,
    value_col: str,
    group_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    order: list | None = None,
    top_n: int | None = None,
    y_max: int | None = None,
    figsize=(7, 3.6),
    cmap_name: str = "viridis"
):
    d = df[[value_col, group_col]].dropna()

    if top_n is not None:
        top_groups = d[group_col].value_counts().head(top_n).index.tolist()
        d = d[d[group_col].isin(top_groups)]

    if order is not None:
        groups = [g for g in order if g in d[group_col].unique()]
    else:
        groups = d[group_col].value_counts().index.tolist()

    data = [d.loc[d[group_col] == g, value_col].values for g in groups]

    fig, ax = plt.subplots(figsize=figsize)

    parts = ax.violinplot(data, showmeans=False, showmedians=True, showextrema=False)

    cmap = plt.get_cmap(cmap_name)
    for i, body in enumerate(parts["bodies"]):
        body.set_facecolor(cmap(i / max(1, len(groups) - 1)))
        body.set_edgecolor("black")
        body.set_alpha(0.85)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.set_xticks(range(1, len(groups) + 1))
    ax.set_xticklabels([str(g) for g in groups], rotation=35, ha="right")

    ax.grid(axis="y", alpha=0.25)

    if y_max is not None:
        ax.set_ylim(0, y_max)

    plt.tight_layout()
    return fig
