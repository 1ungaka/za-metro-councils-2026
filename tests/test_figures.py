from metrocouncils import figures
from metrocouncils.constants import PROCESSED_DIR


def test_figures_and_tables_are_written(tmp_path):
    figure_folder = tmp_path / "figures"
    table_folder = tmp_path / "tables"
    figures.run(figure_folder, table_folder)
    for number in ("1_seat_ranges", "2_largest_party", "3_polls_and_fundamentals", "4_backtest"):
        assert (figure_folder / f"figure_{number}.png").stat().st_size > 1000
    assert (table_folder / "table_buffalo_city_sensitivity.csv").exists()
    assert (PROCESSED_DIR / "forecast" / "parties.csv").exists()


def test_near_certainty_is_never_shown_as_100_percent():
    assert figures.probability_label(0.9994) == ">99%"
    assert figures.probability_label(0.55) == "55%"
