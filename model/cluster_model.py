"""Nearest-centroid labels for the unscaled k=3 skill model.

Centroids are the fitted k-means centers, in cluster-number order:
skill_programming, skill_data_stats, skill_frontend_design, skill_business_pitch.
"""

CENTROIDS = (
    (3.0, 3.5, 1.25, 1.25),
    (2.928571428571429, 3.142857142857143, 2.7857142857142856, 3.9285714285714284),
    (4.2, 4.6, 4.0, 4.6),
)


def predict_cluster(skills):
    """Return the cluster number of the nearest centroid."""
    best_label = 0
    best_distance = None
    for label, centroid in enumerate(CENTROIDS):
        distance = 0.0
        for value, center in zip(skills, centroid):
            diff = value - center
            distance += diff * diff
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_label = label
    return best_label
