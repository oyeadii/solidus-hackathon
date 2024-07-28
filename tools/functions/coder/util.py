import matplotlib.pyplot as plt
from autogen.coding.base import CodeResult
from typing import List
from pydantic import Field
import re
import plotly.tools as tls
import json
from plotly.io import to_json
import matplotlib as mpl
import os


class IPythonCodeResult(CodeResult):
    """(Experimental) A code result class for IPython code executor."""

    output_files: List[dict] = Field(
        default_factory=list,
        description="The list of files that the executed code blocks generated.",
    )


def generate_and_return_plot_json(code):
    local_rc_path = './matplotlibrc'
    if os.path.exists(local_rc_path):
        mpl.rc_file(local_rc_path)

    # Split the code by plt.show() while keeping the plt.show() in the resulting list
    parts = re.split(r'(\bplt\.show\(\s*\))', code)

    # Initialize the result
    fig_dict = {}

    # Loop through the parts and execute the code when plt.show() is encountered
    exec_globals = globals()
    for part in parts:
        sanitized_part = re.sub(r'\bplt\.show\(\s*\)\s*;', '', part)
        sanitized_part = re.sub(r'\bplt\.show\(\s*\)', '', sanitized_part)

        try:
            exec(sanitized_part, exec_globals)

            if 'plt.show()' in part:
                fig = plt.gcf()

                # Extract x-tick and y-tick labels from the matplotlib figure
                ax = plt.gca()
                xticks = ax.get_xticks()
                xticklabels = [tick.get_text() for tick in ax.get_xticklabels()]
                yticks = ax.get_yticks()
                yticklabels = [tick.get_text() for tick in ax.get_yticklabels()]

                # Check if grid is enabled
                xgrid = ax.xaxis._major_tick_kw.get('gridOn', False)
                ygrid = ax.yaxis._major_tick_kw.get('gridOn', False)

                plotly_fig = tls.mpl_to_plotly(fig)

                # Manually set the x-tick and y-tick labels in the plotly figure
                plotly_fig.update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=xticks,
                        ticktext=xticklabels,
                        showgrid=xgrid,  # Show or hide x grid lines based on Matplotlib setting
                    ),
                    yaxis=dict(
                        tickmode='array',
                        tickvals=yticks,
                        ticktext=yticklabels,
                        showgrid=ygrid,  # Show or hide y grid lines based on Matplotlib setting
                    ),
                    plot_bgcolor='white'
                    if ax.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
                    else 'rgba(0,0,0,0)',
                )

                # Ensure gridlines match Matplotlib settings
                if xgrid:
                    plotly_fig.update_xaxes(showgrid=True, gridcolor='lightgrey')
                if ygrid:
                    plotly_fig.update_yaxes(showgrid=True, gridcolor='lightgrey')

                fig_json = to_json(plotly_fig)
                fig_dict = json.loads(fig_json)
                plt.close(
                    fig
                )  # Close the figure to ensure a clean state for the next plot
                break  # Exit after handling the first plt.show()
        except Exception as e:
            fig_dict = {
                "error": str(e)
            }  # Return the error message in case of an exception
            break  # Exit after handling the exception

    # with open("output.json", 'w') as f:
    #     json.dump(fig_dict, f, indent=4)
    return fig_dict


BEFORE_INJECTING_CODE = """
import json
import matplotlib as mpl
import plotly.tools as tls
from plotly.io import to_json
import matplotlib.pyplot as plt

%matplotlib notebook
"""

AFTER_INJECTING_CODE = """
fig_dicts = []
figures = [plt.figure(num) for num in plt.get_fignums()]
for fig in figures:
    fig = plt.gcf()
    # Extract x-tick and y-tick labels from the matplotlib figure
    ax = plt.gca()
    xticks = ax.get_xticks()
    xticklabels = [tick.get_text() for tick in ax.get_xticklabels()]
    yticks = ax.get_yticks()
    yticklabels = [tick.get_text() for tick in ax.get_yticklabels()]

    # Check if grid is enabled
    xgrid = ax.xaxis._major_tick_kw.get('gridOn', False)
    ygrid = ax.yaxis._major_tick_kw.get('gridOn', False)

    plotly_fig = tls.mpl_to_plotly(fig)

    # Manually set the x-tick and y-tick labels in the plotly figure
    plotly_fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=xticks,
            ticktext=xticklabels,
            showgrid=xgrid  # Show or hide x grid lines based on Matplotlib setting
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=yticks,
            ticktext=yticklabels,
            showgrid=ygrid  # Show or hide y grid lines based on Matplotlib setting
        ),
        plot_bgcolor='white' if ax.get_facecolor() == (1.0, 1.0, 1.0, 1.0) else 'rgba(0,0,0,0)'
    )

    # Ensure gridlines match Matplotlib settings
    if xgrid:
        plotly_fig.update_xaxes(showgrid=True, gridcolor='lightgrey')
    if ygrid:
        plotly_fig.update_yaxes(showgrid=True, gridcolor='lightgrey')

    fig_json = to_json(plotly_fig)
    fig_dicts.append(json.loads(fig_json))
    plt.close(fig)  # Close the figure to ensure a clean state for the next plot

%matplotlib inline

print("XXXXXXXXX"+str(json.dumps(fig_dicts))+"XXXXXXXXX")
"""
