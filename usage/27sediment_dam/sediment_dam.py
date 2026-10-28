"""Dam sediment survey/removal scenario with route comparison."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import irsim
from irsim.sediment import SedimentField, compare_routes, hotspot_route, lawnmower_route


def drive_route(route: np.ndarray) -> np.ndarray:
    """Drive an IR-SIM omnidirectional robot through route waypoints."""
    config = Path(__file__).with_name("sediment_dam.yaml")
    env = irsim.make(str(config), display=False, save_ani=False)
    track = [np.asarray(env.robot.state[:2], dtype=float).reshape(2)]
    try:
        for waypoint in route[1:]:
            for _ in range(200):
                position = np.asarray(env.robot.state[:2], dtype=float).reshape(2)
                error = waypoint - position
                distance = float(np.linalg.norm(error))
                if distance <= 0.25:
                    break
                velocity = np.clip(2.5 * error, -3.0, 3.0)
                env.step(velocity)
                track.append(np.asarray(env.robot.state[:2], dtype=float).reshape(2))
            else:
                raise RuntimeError(f"IR-SIM could not reach waypoint {waypoint.tolist()}")
    finally:
        env.end(ending_time=0)
    return np.asarray(track)


def main(output: str = "sediment_route_comparison.png") -> None:
    field = SedimentField.reservoir()
    routes = {
        "Full coverage": lawnmower_route(field.width, field.height),
        "Hotspot first": hotspot_route(field),
    }
    metrics = compare_routes(field)
    tracks = {label: drive_route(route) for label, route in routes.items()}

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    extent = (0, field.width, 0, field.height)
    image = axes[0].imshow(field.thickness, origin="lower", extent=extent, cmap="copper_r")
    axes[0].set(title="Sediment buildup", xlabel="distance along dam (m)", ylabel="width (m)")
    fig.colorbar(image, ax=axes[0], label="sediment thickness (m)")

    colors = ("#0072B2", "#D55E00")
    for axis, (label, route), color, result in zip(axes[1:], routes.items(), colors, metrics, strict=True):
        track = tracks[label]
        axis.imshow(field.thickness, origin="lower", extent=extent, cmap="Greys", alpha=0.45)
        axis.plot(track[:, 0], track[:, 1], color=color, linewidth=1.6, label="IR-SIM track")
        axis.scatter(route[:, 0], route[:, 1], s=8, color=color, label="waypoints")
        axis.set(
            title=f"{label}\n{result.removed_m3:.1f} m³ removed • {result.distance_m:.0f} m travel",
            xlabel="distance along dam (m)",
            ylabel="width (m)",
            xlim=(0, field.width),
            ylim=(0, field.height),
        )
        axis.set_aspect("equal")
        axis.legend(loc="upper right", fontsize=8)

    fig.suptitle("Autonomous sediment-removal route comparison", fontsize=15)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"saved {Path(output).resolve()}")
    for result in metrics:
        print(
            f"{result.name:14} distance={result.distance_m:7.1f} m  "
            f"removed={result.removed_m3:7.2f} m³  mapped={result.mapped_fraction:5.1%}  "
            f"energy-index={result.energy_index:7.1f}"
        )


if __name__ == "__main__":
    main()