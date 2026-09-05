import os
import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt


def _percentile_limits(x, low=1.0, high=99.0):
    x = np.asarray(x)
    finite = x[np.isfinite(x)]
    if finite.size == 0:
        return None, None

    vmin, vmax = np.percentile(finite, [low, high])
    if vmin == vmax:
        vmax = vmin + 1e-12
    return float(vmin), float(vmax)


def _tof_axis_values_and_label(tau, args):
    if getattr(args, "axis", "ns") == "m":
        return tau * 3e8 / 2.0, "distance (m)"
    return tau * 1e9, "ToF (ns)"


def _normalize_axis_name(axis_name):
    aliases = {
        "aoa": "azi",
        "azimuth": "azi",
        "theta": "azi",
        "azi": "azi",
        "tof": "tof",
        "tau": "tof",
        "distance": "tof",
        "doppler": "doppler",
        "fd": "doppler",
    }
    normalized = aliases.get(str(axis_name).lower())
    if normalized is None:
        raise ValueError(f"Unsupported axis name: {axis_name}")
    return normalized


def _axis_values_and_label(axis_name, values, args):
    axis_name = _normalize_axis_name(axis_name)
    if axis_name == "tof":
        return _tof_axis_values_and_label(values, args)
    if axis_name == "azi":
        return values, "Azimuth (deg)"
    if axis_name == "doppler":
        return values, "Doppler frequency (Hz)"
    raise ValueError(f"Unsupported axis name: {axis_name}")


def plot_heatmap(
    frame_idx,
    x_values,
    y_values,
    heatmap,
    args,
    title="",
    cmap="jet",
    x_axis="",
    y_axis="",
    file_suffix=None,
    sdim=None,
):
    x_values, x_label = _axis_values_and_label(x_axis, np.asarray(x_values), args)
    y_values, y_label = _axis_values_and_label(y_axis, np.asarray(y_values), args)
    heatmap = np.asarray(heatmap)
    expected_shape = (len(y_values), len(x_values))
    if heatmap.shape != expected_shape:
        raise ValueError(
            f"Expected heatmap shape {expected_shape}, but got {heatmap.shape}"
        )

    plt.figure()
    plt.pcolormesh(x_values, y_values, heatmap, cmap=cmap, shading="auto")
    if args.colorbar:
        plt.colorbar()

    plt.gca().set_xticks(x_values, minor=True)
    plt.gca().set_yticks(y_values, minor=True)
    plt.grid(which="minor", color="w", linestyle="-", linewidth=0.5, alpha=0.1)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    full_title = title + " @ frame " + str(frame_idx)
    if sdim is not None:
        full_title += " Sdim " + str(int(sdim))
    plt.title(full_title, fontsize=8)

    save_dir = args.pics_dir
    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        filename = f"{frame_idx:04d}.png"
        if file_suffix:
            filename = f"{frame_idx:04d}_{file_suffix}.png"
        save_path = os.path.join(save_dir, filename)
        plt.savefig(save_path, dpi=100)
        plt.close()
        print(f"Saved: {save_path}")


def _plot_target_gt(ax, target_gt, x_axis, y_axis, args):
    """Plot ``[azimuth, ToF, Doppler]`` ground-truth rows on selected axes."""
    target_gt = getattr(args, "target_gt", None) if target_gt is None else target_gt
    if target_gt is None:
        return

    target_gt = np.asarray(target_gt, dtype=float)
    if target_gt.size == 0:
        return
    target_gt = np.atleast_2d(target_gt)
    if target_gt.shape[1] != 3:
        raise ValueError(
            "target_gt must have shape (num_targets, 3) with rows "
            "[azimuth_deg, tof_s, doppler_hz]."
        )

    column_by_axis = {"azi": 0, "tof": 1, "doppler": 2}
    x_gt, _ = _axis_values_and_label(
        x_axis, target_gt[:, column_by_axis[x_axis]], args
    )
    y_gt, _ = _axis_values_and_label(
        y_axis, target_gt[:, column_by_axis[y_axis]], args
    )
    ax.scatter(
        x_gt,
        y_gt,
        marker="x",
        s=50,
        color="white",
        linewidths=1.5,
        zorder=3,
    )


def plot_spectrum(
    frame_idx,
    axis0_values,
    axis1_values,
    P_music,
    args,
    title="",
    x_axis=None,
    y_axis=None,
    sdim=None,
    spectrum_axes=None,
    ax=None,
    save=True,
    show_colorbar=None,
    target_gt=None,
):
    if spectrum_axes is None or len(spectrum_axes) != 2:
        raise ValueError("spectrum_axes=(axis0, axis1) is required.")

    axis0, axis1 = map(_normalize_axis_name, spectrum_axes)
    x_axis = _normalize_axis_name(x_axis or axis1)
    y_axis = _normalize_axis_name(y_axis or axis0)
    if {x_axis, y_axis} != {axis0, axis1}:
        raise ValueError("x_axis/y_axis must match spectrum_axes.")

    axis0_values = np.asarray(axis0_values)
    axis1_values = np.asarray(axis1_values)
    P_music = np.asarray(P_music)
    if P_music.shape != (len(axis0_values), len(axis1_values)):
        raise ValueError(
            f"Expected spectrum shape {(len(axis0_values), len(axis1_values))}, "
            f"got {P_music.shape}."
        )

    values_by_axis = {axis0: axis0_values, axis1: axis1_values}
    x_values, x_label = _axis_values_and_label(x_axis, values_by_axis[x_axis], args)
    y_values, y_label = _axis_values_and_label(y_axis, values_by_axis[y_axis], args)
    plot_values = P_music.T if x_axis == axis0 else P_music

    if ax is None:
        _, ax = plt.subplots()
    mesh = ax.pcolormesh(
        x_values,
        y_values,
        plot_values,
        cmap='jet',
        shading='auto',
    )
    if show_colorbar is None:
        show_colorbar = bool(args.colorbar)
    if show_colorbar:
        ax.figure.colorbar(mesh, ax=ax)
    _plot_target_gt(ax, target_gt, x_axis, y_axis, args)

    # 畫出網格線 (選擇性開啟，用於觀察 Grid Refinement 的分佈)
    ax.set_xticks(x_values, minor=True)
    ax.set_yticks(y_values, minor=True)
    ax.grid(which='minor', color='w', linestyle='-', linewidth=0.5, alpha=0.2)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    full_title = title + ' @ frame ' + str(frame_idx)
    if sdim is not None:
        full_title += ' Sdim ' + str(int(sdim))
    ax.set_title(full_title, fontsize=8)

    # --- save figures ---
    save_dir = args.pics_dir
    if save and save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(
            save_dir, f"{title} {frame_idx:04d}.png"
        )
        ax.figure.savefig(save_path, dpi=100)
        plt.close(ax.figure)
        print(f"Saved: {save_path}")

    return ax
