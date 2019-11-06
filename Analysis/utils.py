import numpy as np
import itertools

def gsr_to_ohm(serial_port_reading, calibration_value=2800):
    """
    Original formula from http://wiki.seeedstudio.com/Grove-GSR_Sensor/:
    Human Resistance = ((1024+2*Serial_Port_Reading)*10000)/(512-Serial_Port_Reading),
    unit is ohm, Serial_Port_Reading is the value display on Serial Port(between 0~1023)

    We have the range 0~4095, and calibration_value != 512.
    Then I think the formula should be the following:
    Human Resistance = ((4096+2*Serial_Port_Reading)*10000)/(calibration_value-Serial_Port_Reading),

    """
    resistance = ((4096 + 2 * serial_port_reading) * 10000) / (calibration_value - serial_port_reading)

    return resistance


def get_interval_from_moment(moment, interval_start, interval_end):
    return [moment + interval_start, moment + interval_end]

def get_intervals_from_moments(moments, interval_start=-3, interval_end=3):
    intervals = []

    for moment in moments:
        interval = get_interval_from_moment(moment, interval_start=interval_start, interval_end=interval_end)
        intervals.append(interval)

    return intervals

class EventIntervals:

    def __init__(self, intervals_list, label, color):
        self.intervals_list = intervals_list
        self.label = label
        self.color = color

    @staticmethod
    def get_mask_interval(time_column, interval):
        interval_start, interval_end = interval
        mask = (interval_start <= time_column) & (time_column <= interval_end)
        return mask

    def get_mask_intervals(self, time_column):
        # One mask for each interval
        masks_list = []

        for interval in self.intervals_list:
            mask_interval = self.get_mask_interval(time_column, interval)
            masks_list.append(mask_interval)

        return masks_list

    def get_mask_intervals_union(self, time_column):
        ### One mask for all intervals
        mask_union = np.zeros(shape=time_column.shape, dtype=bool)

        masks_list = self.get_mask_intervals(time_column)
        for mask in masks_list:
            mask_union = mask_union | mask.values

        return mask_union


def get_aspect_from_n_plots(n_plots):
    row = col = int(n_plots ** 0.5)
    if row * col >= n_plots:
        return row, col
    else:
        row += 1
        if row * col >= n_plots:
            return row, col
        else:
            col += 1
            if row * col >= n_plots:
                return row, col
            else:
                raise ValueError(f'Can\'t find aspect ratio for {n_plots}')


def plot_measurements(
        analyser_column_pairs_list,  # analysers for hrm, temperature, etc. for the same session_id
        pic_prefix,
        session_id,
        event_intervals_list=None,
        n_rows=None,
        n_cols=None,
        figsize=(21, 15),
        plot_suptitle=False,
        fontsize=18,
        alpha=0.9,
        alpha_background=0.5,
        sharex='col',
        linewidth=1,
):
    n_plots = len(analyser_column_pairs_list)

    if n_rows is None:  # TODO: can be isolated to a function
        if n_cols is None:
            n_rows, n_cols = get_aspect_from_n_plots(n_plots)
        else:
            n_rows = int(np.ceil(n_plots / n_cols))
    else:
        if n_cols is None:
            n_cols = int(np.ceil(n_plots / n_rows))

    analysers_names = [analyser.sensor_name for analyser, column in analyser_column_pairs_list]
    analysers_names = list(OrderedDict.fromkeys(analysers_names))  # To preserve uniqueness and order
    pic_path = pic_prefix + 'measurements_' + '_'.join(analysers_names) + f'_{session_id}' + '.png'

    fig, ax_list = plt.subplots(n_rows, n_cols, sharex=sharex, figsize=figsize, squeeze=False)
    rows_cols_list = itertools.product(range(n_rows), range(n_cols))

    for analyser_column_pair, row_col_pair in zip(analyser_column_pairs_list, rows_cols_list):
        analyser, column = analyser_column_pair
        n_row, n_col = row_col_pair
        ax = ax_list[n_row, n_col]

        times = analyser.df['time']
        data2plot = analyser.df[column]
        sensor_name = analyser.sensor_name

        # ax.plot(times, data2plot.values, label='nothing', color='black', alpha=alpha_background)
        ax.plot(times, data2plot.values, color='black', alpha=alpha_background)
        ax.tick_params(axis='both', labelsize=fontsize-8)
        # ax.set_ylabel(column, fontsize=fontsize)
        column_text = 'chair ' + column if (column.startswith('acc') or column.startswith('gyro')) else column
        column_text = 'heart rate' if column_text == 'hrm' else column_text
        column_text = 'skin resistance' if column_text =='resistance' else column_text
        column_text = 'muscle activity' if column_text =='muscle_activity' else column_text
        ax.set_title(column_text, fontsize=fontsize)
        if n_row == n_rows - 1:
            ax.set_xlabel('time, s', fontsize=fontsize + 7)

        for event_intervals in event_intervals_list:
            # intervals_list = event_intervals.intervals_list
            event_label = event_intervals.label
            color = event_intervals.color
            # mask_interval_list = get_mask_intervals(times, intervals_list=intervals_list)
            mask_interval_list = event_intervals.get_mask_intervals(times)

            for mask_interval in mask_interval_list:
                times_with_mask = times.loc[mask_interval]
                data2plot_with_mask = data2plot.loc[mask_interval]
                ax.plot(
                    times_with_mask,
                    data2plot_with_mask.values,
                    # label=event_label,
                    color=color,
                    alpha=alpha,
                    linewidth=linewidth,
                )

            ax.plot([], [], label=event_label, color=color)
        ax.legend(loc='upper right', fontsize=fontsize-8)  # maybe the constant could be generalized

    if plot_suptitle:  # TODO: deal with suptitle
        suptitle = f'{sensor_name.capitalize()} sensors data, session_id = {session_id}'  # TODO: adapt for multiple case
        fig.suptitle(suptitle, fontsize=fontsize + 2)

    # fig.tight_layout(rect=[0, 0.00, 1, 0.9625])
    fig.tight_layout(rect=[0, 0.00, 1, 1])

    # fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    # fig.subplots_adjust(top=0.5)
    # fig.tight_layout()
    # plt.savefig(pic_prefix + f'measurements_{self.sensor_name}_{self.session_id}.png')
    plt.savefig(pic_path)
    plt.close()

