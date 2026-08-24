"""Shared Hypothesis strategies for property-based testing across the engine."""

from hypothesis import strategies as st

draw_positions = st.floats(min_value=-10000, max_value=10000)
velocity_vectors = st.floats(min_value=-2000, max_value=2000)
health_values = st.floats(min_value=0.0, max_value=100.0)
frame_deltas = st.floats(min_value=0.0, max_value=1.0)
unit_intervals = st.floats(min_value=0.0, max_value=1.0)
positive_floats = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
color_channels = st.integers(min_value=0, max_value=255)
rgb_colors = st.tuples(color_channels, color_channels, color_channels)


def collision_rect_lists(
    min_size: int = 0, max_size: int = 20,
    world_size: float = 2000.0,
) -> st.SearchStrategy[list[tuple[float, float, float, float]]]:
    """Generate lists of (x, y, w, h) collision rects within world_size bounds."""
    return st.lists(
        st.tuples(
            st.floats(min_value=-world_size, max_value=world_size),
            st.floats(min_value=-world_size, max_value=world_size),
            st.floats(min_value=1.0, max_value=200.0),
            st.floats(min_value=1.0, max_value=200.0),
        ),
        min_size=min_size, max_size=max_size,
    )
