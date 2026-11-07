import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle, Circle
fig, ax = plt.subplots(figsize=(10, 7.5)); ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis("off")
ax.add_patch(Rectangle((2.3, 0.2), 5.4, 7.6, fill=False, lw=1.5, ec="#333"))
ax.text(5, 7.55, "Doctor Appointment Booking System", ha="center", fontsize=11, weight="bold")
def actor(x, y, name):
    ax.add_patch(Circle((x, y+0.55), 0.18, fill=False, lw=1.5))
    ax.plot([x, x], [y+0.37, y-0.1], c="k", lw=1.5); ax.plot([x-0.3, x+0.3], [y+0.25, y+0.25], c="k", lw=1.5)
    ax.plot([x, x-0.25], [y-0.1, y-0.5], c="k", lw=1.5); ax.plot([x, x+0.25], [y-0.1, y-0.5], c="k", lw=1.5)
    ax.text(x, y-0.85, name, ha="center", fontsize=11, weight="bold")
cases = {
 "Register / Login": (5, 6.7), "Search doctors": (5, 5.9), "Book appointment": (5, 5.1),
 "View / Cancel appointment": (5, 4.3), "View appointment requests": (5, 3.5),
 "Approve / Reject / Complete": (5, 2.7), "Add / Remove doctor": (5, 1.9), "View statistics & all appointments": (5, 1.1)}
for t, (x, y) in cases.items():
    ax.add_patch(Ellipse((x, y), 3.6, 0.65, fc="#eaf2ff", ec="#0d6efd", lw=1.3)); ax.text(x, y, t, ha="center", va="center", fontsize=9.5)
actor(1, 5.2, "Patient"); actor(1, 2.7, "Doctor"); actor(9, 3.4, "Admin")
def link(a, c):
    x, y = a; cx, cy = cases[c]; ax.plot([x + (0.3 if x < 5 else -0.3), cx + (-1.8 if x < 5 else 1.8)], [y+0.2, cy], c="#555", lw=1)
for c in ["Register / Login", "Search doctors", "Book appointment", "View / Cancel appointment"]: link((1, 5.2), c)
for c in ["Register / Login", "View appointment requests", "Approve / Reject / Complete"]: link((1, 2.7), c)
for c in ["Register / Login", "Add / Remove doctor", "View statistics & all appointments"]: link((9, 3.4), c)
plt.savefig("usecase.png", dpi=170, bbox_inches="tight", facecolor="white")
