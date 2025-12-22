import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_bar_counts(
    counts: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str = "Count",
    top_n: int | None = 12,
    figsize=(1, 3),
    cmap_name: str = "viridis"
):
    """
    Bar plot for value counts with a nicer palette + smaller size.
    """
    counts = counts.dropna()

    # optionally limit categories so plot stays readable
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


# def plot_bar_grouped(
#     df: pd.DataFrame,
#     x_col: str,
#     y_col: str,
#     title: str,
#     xlabel: str,
#     ylabel: str,
#     figsize=(6.5, 3.4),
#     cmap_name: str = "viridis"
# ):
#     """
#     Simple bar plot for pre-aggregated data: x_col categories vs y_col numeric values.
#     """
#     fig, ax = plt.subplots(figsize=figsize)

#     cmap = plt.get_cmap(cmap_name)
#     colors = [cmap(i) for i in range(len(df))]

#     ax.bar(df[x_col].astype(str), df[y_col], color=colors)

#     ax.set_title(title)
#     ax.set_xlabel(xlabel)
#     ax.set_ylabel(ylabel)

#     ax.grid(axis="y", alpha=0.25)
#     plt.xticks(rotation=35, ha="right")
#     plt.tight_layout()

#     return fig


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


# def plot_box_by_group(
#     df: pd.DataFrame,
#     value_col: str,
#     group_col: str,
#     title: str,
#     xlabel: str,
#     ylabel: str,
#     top_n: int = 6,
#     figsize=(7, 3.6)
# ):
#     """
#     Boxplot of numeric values grouped by category.
#     Only shows top_n groups by frequency to keep it readable.
#     """
#     d = df[[value_col, group_col]].dropna()

#     top_groups = d[group_col].value_counts().head(top_n).index
#     d = d[d[group_col].isin(top_groups)]

#     groups = [d.loc[d[group_col] == g, value_col].values for g in top_groups]

#     fig, ax = plt.subplots(figsize=figsize)
#     ax.boxplot(groups, labels=[str(g) for g in top_groups], showfliers=False)

#     ax.set_title(title)
#     ax.set_xlabel(xlabel)
#     ax.set_ylabel(ylabel)

#     ax.grid(axis="y", alpha=0.25)
#     plt.xticks(rotation=35, ha="right")
#     plt.tight_layout()

#     return fig


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

import numpy as np


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
    """
    Scatter plot for two numeric variables.
    """
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
    """
    Boxplot of a numeric column by categories (top_n by frequency).
    Hides extreme outliers for readability.
    """
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
